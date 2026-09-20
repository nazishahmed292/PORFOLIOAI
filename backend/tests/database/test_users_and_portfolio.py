"""Accounts, profile, skills, projects, experience, education: rules the database enforces."""

from datetime import date

import pytest
from sqlalchemy import delete, select, text

from app.models import (
    Education,
    Experience,
    Profile,
    Project,
    ProjectStatus,
    Skill,
    SkillCategory,
    User,
    UserRole,
    project_skills,
)

from .factories import make_project, make_skill, make_user
from .helpers import count


# ---- users & profile -----------------------------------------------------------------


def test_server_defaults_fill_in_omitted_columns(db):
    """Raw SQL that names only the required columns: the *database* supplies the rest."""
    db.execute(
        text("INSERT INTO users (email, hashed_password, full_name) VALUES ('a@x.com', 'h', 'A')")
    )
    row = db.execute(text("SELECT role, is_active, created_at, updated_at FROM users")).one()
    assert row.role == "admin"
    assert bool(row.is_active) is True
    assert row.created_at is not None and row.updated_at is not None


def test_user_roundtrip_returns_enum(db):
    user = make_user(db, role=UserRole.VIEWER)
    db.expire_all()
    assert db.get(User, user.id).role is UserRole.VIEWER


def test_email_must_be_lowercase(db, insert_rejected):
    insert_rejected(
        User(email="Ann@Example.com", hashed_password="h", full_name="Ann"), by="ck_users_email_lowercase"
    )


def test_email_is_unique(db, insert_rejected):
    make_user(db, email="ann@example.com")
    insert_rejected(
        User(email="ann@example.com", hashed_password="h", full_name="Other"),
        by=r"ix_users_email|users\.email",
    )


def test_role_outside_the_enum_is_rejected_by_the_database(db):
    from sqlalchemy.exc import IntegrityError

    with pytest.raises(IntegrityError, match="ck_users_user_role"):
        db.execute(
            text("INSERT INTO users (email, hashed_password, full_name, role) VALUES ('b@x.com','h','B','root')")
        )
    db.rollback()


def test_a_user_has_at_most_one_profile(db, insert_rejected):
    user = make_user(db)
    db.add(Profile(user_id=user.id, full_name="One"))
    db.flush()
    insert_rejected(Profile(user_id=user.id, full_name="Two"), by=r"ix_profiles_user_id|profiles\.user_id")


def test_deleting_a_user_deletes_their_profile(db):
    user = make_user(db)
    db.add(Profile(user_id=user.id, full_name="Owner", open_to_work=True))
    db.flush()
    assert count(db, Profile) == 1

    db.execute(delete(User).where(User.id == user.id))  # SQL delete: no ORM cascade involved
    assert count(db, Profile) == 0


def test_profile_needs_an_existing_user(db, insert_rejected):
    insert_rejected(  # proves foreign keys are enforced
        Profile(user_id=424242, full_name="Ghost"), by=r"fk_profiles_user_id_users|FOREIGN KEY"
    )


# ---- skills --------------------------------------------------------------------------


def test_skill_defaults(db):
    skill = make_skill(db, "PyTorch")
    db.refresh(skill)
    assert skill.category is SkillCategory.OTHER
    assert skill.proficiency == 3


@pytest.mark.parametrize("proficiency", [1, 5])
def test_skill_proficiency_accepts_the_range_ends(db, proficiency):
    assert make_skill(db, f"S{proficiency}", proficiency=proficiency).id


@pytest.mark.parametrize("proficiency", [0, 6, -1])
def test_skill_proficiency_outside_1_to_5_is_rejected(db, insert_rejected, proficiency):
    insert_rejected(Skill(name="X", slug="x", proficiency=proficiency), by="ck_skills_proficiency_range")


def test_skill_slug_is_unique_and_lowercase(db, insert_rejected):
    make_skill(db, "Python")
    insert_rejected(Skill(name="python", slug="python"), by=r"ix_skills_slug|skills\.slug")
    insert_rejected(Skill(name="Rust", slug="Rust"), by="ck_skills_slug_lowercase")


def test_negative_years_of_experience_is_rejected(db, insert_rejected):
    insert_rejected(Skill(name="Go", slug="go", years_experience=-0.5), by="ck_skills_years_positive")


# ---- projects ------------------------------------------------------------------------


def test_project_roundtrip_with_json_and_enum(db):
    project = make_project(
        db,
        "cancerbind",
        status=ProjectStatus.IN_PROGRESS,
        highlights=["GAT encoder", "affinity head"],
        start_date=date(2026, 1, 1),
    )
    db.expire_all()
    loaded = db.get(Project, project.id)
    assert loaded.highlights == ["GAT encoder", "affinity head"]
    assert loaded.status is ProjectStatus.IN_PROGRESS
    # the stored text is the enum *value*, which is what a raw SQL reader sees
    assert db.execute(text("SELECT status FROM projects")).scalar_one() == "in_progress"


def test_project_json_default_is_an_empty_list(db):
    project = make_project(db)
    db.expire_all()
    assert db.get(Project, project.id).highlights == []


def test_project_slug_is_unique(db, insert_rejected):
    make_project(db, "quantahire")
    insert_rejected(
        Project(slug="quantahire", title="Copy", summary="s"), by=r"ix_projects_slug|projects\.slug"
    )


def test_project_end_date_cannot_precede_start_date(db, insert_rejected):
    insert_rejected(
        Project(slug="p", title="P", summary="s", start_date=date(2026, 5, 1), end_date=date(2026, 4, 1)),
        by="ck_projects_dates_ordered",
    )


def test_project_skills_many_to_many(db):
    python, torch = make_skill(db, "Python"), make_skill(db, "PyTorch")
    project = make_project(db)
    project.skills = [python, torch]
    db.flush()
    db.expire_all()
    assert {s.slug for s in db.get(Project, project.id).skills} == {"python", "pytorch"}
    assert [p.id for p in db.get(Skill, python.id).projects] == [project.id]


def test_the_same_skill_cannot_be_linked_twice(db):
    from sqlalchemy.exc import IntegrityError

    skill, project = make_skill(db), make_project(db)
    link = {"project_id": project.id, "skill_id": skill.id}
    db.execute(project_skills.insert().values(**link))
    with pytest.raises(IntegrityError):
        db.execute(project_skills.insert().values(**link))
    db.rollback()


def test_deleting_a_project_removes_links_but_keeps_skills(db):
    skill, project = make_skill(db), make_project(db)
    db.execute(project_skills.insert().values(project_id=project.id, skill_id=skill.id))

    db.execute(delete(Project).where(Project.id == project.id))
    assert db.execute(select(project_skills)).all() == []
    assert count(db, Skill) == 1


def test_deleting_a_skill_removes_links_but_keeps_projects(db):
    skill, project = make_skill(db), make_project(db)
    db.execute(project_skills.insert().values(project_id=project.id, skill_id=skill.id))

    db.execute(delete(Skill).where(Skill.id == skill.id))
    assert db.execute(select(project_skills)).all() == []
    assert count(db, Project) == 1


# ---- experience & education ----------------------------------------------------------


def test_current_role_without_end_date_is_accepted(db):
    db.add(Experience(company="Acme", title="ML Intern", start_date=date(2026, 1, 1), is_current=True))
    db.flush()
    assert count(db, Experience) == 1


def test_current_role_cannot_have_an_end_date(db, insert_rejected):
    insert_rejected(
        Experience(
            company="Acme", title="Dev", start_date=date(2025, 1, 1), end_date=date(2025, 6, 1), is_current=True
        ),
        by="ck_experiences_current_has_no_end",
    )


def test_experience_end_cannot_precede_start(db, insert_rejected):
    insert_rejected(
        Experience(company="Acme", title="Dev", start_date=date(2025, 6, 1), end_date=date(2025, 1, 1)),
        by="ck_experiences_dates_ordered",
    )


def test_experience_achievements_roundtrip(db):
    row = Experience(
        company="Acme", title="Dev", start_date=date(2025, 1, 1), achievements=["Cut latency 40%", "Shipped v2"]
    )
    db.add(row)
    db.flush()
    db.expire_all()
    assert db.get(Experience, row.id).achievements == ["Cut latency 40%", "Shipped v2"]


def test_education_end_cannot_precede_start(db, insert_rejected):
    insert_rejected(
        Education(institution="U", degree="B.Tech", start_date=date(2026, 1, 1), end_date=date(2025, 1, 1)),
        by="ck_education_dates_ordered",
    )
