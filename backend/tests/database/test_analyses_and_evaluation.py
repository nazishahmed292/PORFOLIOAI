"""Job/resume analyzers and the RAG evaluation tables."""

from datetime import datetime, timezone

import pytest
from sqlalchemy import delete, select, text

from app.models import (
    EvaluationQuestion,
    EvaluationResult,
    EvaluationRun,
    FailureType,
    JobAnalysis,
    QuestionCategory,
    ResumeAnalysis,
    RetrievalMode,
    RunStatus,
    User,
)

from .factories import make_question, make_run, make_user
from .helpers import count

UTC = timezone.utc


def result(run, question, **overrides) -> EvaluationResult:
    return EvaluationResult(run_id=run.id, question_id=question.id, **overrides)


# ---- analyzers -----------------------------------------------------------------------


def test_job_analysis_roundtrip(db):
    row = JobAnalysis(
        job_title="ML Engineer",
        job_description="Build RAG systems.",
        match_score=82.5,
        matched_skills=["Python", "PyTorch"],
        missing_skills=["Kubernetes"],
        evidence=[{"chunk_id": 7, "title": "CancerBind report", "score": 0.81}],
    )
    db.add(row)
    db.flush()
    db.expire_all()
    loaded = db.get(JobAnalysis, row.id)
    assert loaded.match_score == 82.5
    assert loaded.missing_skills == ["Kubernetes"]
    assert loaded.evidence[0]["chunk_id"] == 7
    assert loaded.recommendations == []  # JSON default


@pytest.mark.parametrize("score", [0, 100])
def test_job_score_accepts_the_range_ends(db, score):
    db.add(JobAnalysis(job_title="T", job_description="d", match_score=score))
    db.flush()


@pytest.mark.parametrize("score", [-0.1, 100.5])
def test_job_score_outside_0_to_100_is_rejected(db, insert_rejected, score):
    insert_rejected(
        JobAnalysis(job_title="T", job_description="d", match_score=score),
        by="ck_job_analyses_score_range",
    )


@pytest.mark.parametrize("score", [-1, 101])
def test_resume_score_outside_0_to_100_is_rejected(db, insert_rejected, score):
    insert_rejected(
        ResumeAnalysis(resume_text="text", overall_score=score), by="ck_resume_analyses_score_range"
    )


def test_deleting_the_user_keeps_their_analyses(db):
    user = make_user(db)
    job = JobAnalysis(user_id=user.id, job_title="T", job_description="d", match_score=50)
    resume = ResumeAnalysis(user_id=user.id, resume_text="cv", overall_score=70)
    db.add_all([job, resume])
    db.flush()

    db.execute(delete(User).where(User.id == user.id))
    db.refresh(job)
    db.refresh(resume)
    assert job.user_id is None and resume.user_id is None


# ---- evaluation questions & runs -----------------------------------------------------


def test_question_defaults(db):
    question = make_question(db)
    db.refresh(question)
    assert question.category is QuestionCategory.FACTUAL
    assert question.is_answerable is True
    assert question.dataset == "default"
    assert question.expected_sources == []


def test_unanswerable_question_has_no_ground_truth(db):
    question = make_question(
        db, question="What is the owner's favourite colour?", category=QuestionCategory.UNANSWERABLE,
        is_answerable=False, ground_truth=None,
    )
    db.expire_all()
    loaded = db.get(EvaluationQuestion, question.id)
    assert loaded.is_answerable is False and loaded.ground_truth is None


def test_run_defaults(db):
    run = make_run(db)
    db.refresh(run)
    assert run.status is RunStatus.PENDING
    assert run.top_k == 5 and run.question_count == 0
    assert run.config == {} and run.metrics == {}


def test_run_metrics_and_config_roundtrip(db):
    run = make_run(
        db,
        retrieval_mode=RetrievalMode.HYBRID_RERANK,
        config={"chunk_size": 512, "overlap": 64},
        metrics={"hit_rate": 0.9, "mrr": 0.71, "per_category": {"skills": 1.0}},
    )
    db.expire_all()
    loaded = db.get(EvaluationRun, run.id)
    assert loaded.retrieval_mode is RetrievalMode.HYBRID_RERANK
    assert loaded.metrics["per_category"] == {"skills": 1.0}
    assert loaded.config["chunk_size"] == 512


def test_run_needs_a_positive_top_k(db, insert_rejected):
    insert_rejected(
        EvaluationRun(name="bad", retrieval_mode=RetrievalMode.DENSE, top_k=0),
        by="ck_evaluation_runs_top_k_positive",
    )


def test_run_cannot_finish_before_it_starts(db, insert_rejected):
    insert_rejected(
        EvaluationRun(
            name="time travel",
            retrieval_mode=RetrievalMode.BM25,
            started_at=datetime(2026, 9, 19, 12, tzinfo=UTC),
            finished_at=datetime(2026, 9, 19, 11, tzinfo=UTC),
        ),
        by="ck_evaluation_runs_times_ordered",
    )


def test_run_times_may_be_partially_unset(db):
    make_run(db, started_at=datetime(2026, 9, 19, 12, tzinfo=UTC))  # still running: no finish time
    make_run(db)
    assert count(db, EvaluationRun) == 2


def test_retrieval_mode_outside_the_enum_is_rejected(db):
    from sqlalchemy.exc import IntegrityError

    with pytest.raises(IntegrityError, match="ck_evaluation_runs_retrieval_mode"):
        db.execute(text("INSERT INTO evaluation_runs (name, retrieval_mode) VALUES ('r', 'magic')"))
    db.rollback()


# ---- evaluation results --------------------------------------------------------------


def test_result_defaults_and_roundtrip(db):
    run, question = make_run(db), make_question(db)
    row = result(
        run, question,
        retrieved_chunk_ids=[12, 7, 31], retrieved_scores=[0.91, 0.84, 0.62],
        hit=True, reciprocal_rank=1.0, precision_at_k=0.4, recall_at_k=1.0,
        faithfulness=0.95, answer_relevance=0.88, latency_ms=1420, answer="CancerBind predicts affinity.",
    )
    db.add(row)
    db.flush()
    db.expire_all()
    loaded = db.get(EvaluationResult, row.id)
    assert loaded.retrieved_chunk_ids == [12, 7, 31]
    assert loaded.retrieved_scores == [0.91, 0.84, 0.62]
    assert loaded.hit is True
    assert loaded.failure_type is FailureType.NONE  # default when nothing went wrong


def test_metrics_may_be_null_until_computed(db):
    run, question = make_run(db), make_question(db)
    db.add(result(run, question))
    db.flush()  # a fresh result row has no scores yet


@pytest.mark.parametrize("metric", ["reciprocal_rank", "precision_at_k", "recall_at_k", "faithfulness", "answer_relevance"])
@pytest.mark.parametrize("value", [-0.01, 1.01])
def test_metrics_must_stay_between_0_and_1(db, insert_rejected, metric, value):
    run, question = make_run(db), make_question(db)
    insert_rejected(result(run, question, **{metric: value}), by=f"ck_evaluation_results_{metric}_range")


@pytest.mark.parametrize("value", [0.0, 1.0])
def test_metric_range_ends_are_valid(db, value):
    run, question = make_run(db), make_question(db)
    db.add(result(run, question, faithfulness=value))
    db.flush()


def test_a_question_has_one_result_per_run(db, insert_rejected):
    run, question = make_run(db), make_question(db)
    db.add(result(run, question))
    db.flush()
    insert_rejected(
        result(run, question),
        by=r"uq_evaluation_results_run_id_question_id|evaluation_results\.run_id",
    )
    other_run = make_run(db, name="second run")
    db.add(result(other_run, question))  # same question in another run is fine
    db.flush()


def test_failure_type_outside_the_enum_is_rejected(db):
    from sqlalchemy.exc import IntegrityError

    run, question = make_run(db), make_question(db)
    with pytest.raises(IntegrityError, match="ck_evaluation_results_failure_type"):
        db.execute(
            text("INSERT INTO evaluation_results (run_id, question_id, failure_type) VALUES (:r, :q, 'gremlins')"),
            {"r": run.id, "q": question.id},
        )
    db.rollback()


def test_result_can_record_a_specific_failure(db):
    run, question = make_run(db), make_question(db)
    row = result(run, question, failure_type=FailureType.HALLUCINATION, failure_notes="Invented a 2019 job.")
    db.add(row)
    db.flush()
    db.expire_all()
    assert db.get(EvaluationResult, row.id).failure_type is FailureType.HALLUCINATION


def test_failure_types_can_be_grouped_for_the_dashboard(db):
    run, question_a, question_b = make_run(db), make_question(db), make_question(db)
    db.add_all(
        [
            result(run, question_a, failure_type=FailureType.RETRIEVAL_MISS),
            result(run, question_b, failure_type=FailureType.RETRIEVAL_MISS),
        ]
    )
    db.flush()
    rows = db.execute(
        select(EvaluationResult.failure_type, text("count(*)")).group_by(EvaluationResult.failure_type)
    ).all()
    assert [(r[0], r[1]) for r in rows] == [(FailureType.RETRIEVAL_MISS, 2)]


def test_deleting_a_run_deletes_its_results_but_not_the_questions(db):
    run, question = make_run(db), make_question(db)
    db.add(result(run, question))
    db.flush()

    db.execute(delete(EvaluationRun).where(EvaluationRun.id == run.id))
    assert count(db, EvaluationResult) == 0
    assert count(db, EvaluationQuestion) == 1


def test_deleting_a_question_deletes_its_results_but_not_the_run(db):
    run, question = make_run(db), make_question(db)
    db.add(result(run, question))
    db.flush()

    db.execute(delete(EvaluationQuestion).where(EvaluationQuestion.id == question.id))
    assert count(db, EvaluationResult) == 0
    assert count(db, EvaluationRun) == 1


def test_deleting_the_creator_keeps_the_run(db):
    user = make_user(db)
    run = make_run(db, created_by=user.id)
    db.execute(delete(User).where(User.id == user.id))
    db.refresh(run)
    assert run.created_by is None
