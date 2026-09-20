import { ArrowRight, BookMarked, FileSearch, SearchCheck } from "lucide-react";
import { Link } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

/** Small amber marker that ties a sentence to a numbered source. */
function Cite({ n }: { n: number }) {
  return (
    <sup className="ml-0.5 inline-flex size-4 items-center justify-center rounded bg-citation align-baseline text-[0.625rem] font-bold text-citation-foreground">
      {n}
    </sup>
  );
}

const EXAMPLE_SOURCES = [
  { n: 1, name: "Code Plagiarism Pattern Detector", section: "Projects" },
  { n: 2, name: "NLP Spam Email Detection", section: "Projects" },
  { n: 3, name: "Restaurant Rating Prediction", section: "Projects" },
];

const HOW_IT_WORKS = [
  {
    icon: SearchCheck,
    title: "Retrieve",
    text: "Your question is matched against the portfolio: projects, skills, experience and uploaded documents.",
  },
  {
    icon: BookMarked,
    title: "Cite",
    text: "The answer is written only from what was found, and every claim points back to its source.",
  },
  {
    icon: FileSearch,
    title: "Admit gaps",
    text: "If the portfolio doesn't cover the question, the assistant says so instead of guessing.",
  },
];

export default function Home() {
  return (
    <div className="space-y-20 sm:space-y-28">
      <section className="grid items-center gap-12 lg:grid-cols-[1fr_1.05fr] lg:gap-16">
        <div>
          <h1 className="text-4xl font-semibold sm:text-5xl lg:text-6xl">
            Ask this portfolio anything.
          </h1>
          <p className="mt-5 max-w-xl text-lg text-muted-foreground">
            Answers come from the projects, skills and experience on file, and each one shows the
            source it was drawn from.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Button asChild size="lg">
              <Link to="/chat">
                Start a conversation <ArrowRight />
              </Link>
            </Button>
            <Button asChild size="lg" variant="outline">
              <Link to="/projects">Browse projects</Link>
            </Button>
          </div>
        </div>

        {/* The one orchestrated moment: an example cited answer builds line by line. */}
        <figure
          className="rounded-xl border bg-card p-5 shadow-sm sm:p-6"
          aria-label="Example conversation with source citations"
        >
          <div className="mb-4 flex items-center justify-between">
            <figcaption className="text-sm font-medium text-muted-foreground">Example conversation</figcaption>
            <Badge variant="outline">Sources shown</Badge>
          </div>

          <div className="space-y-4">
            <div className="animate-line-in ml-auto w-fit max-w-[85%] rounded-2xl rounded-br-sm bg-primary px-4 py-2.5 text-sm text-primary-foreground">
              Which projects here use Python?
            </div>

            <div
              className="animate-line-in max-w-[92%] rounded-2xl rounded-bl-sm bg-muted px-4 py-3 text-sm leading-relaxed"
              style={{ animationDelay: "0.7s" }}
            >
              Three projects use Python: the Code Plagiarism Pattern Detector
              <Cite n={1} />, the NLP Spam Email Detection model
              <Cite n={2} />, and Restaurant Rating Prediction
              <Cite n={3} />.
            </div>

            <ul className="animate-line-in space-y-1.5 pl-1" style={{ animationDelay: "1.5s" }}>
              {EXAMPLE_SOURCES.map((source) => (
                <li key={source.n} className="flex items-center gap-2 text-sm">
                  <span className="inline-flex size-5 shrink-0 items-center justify-center rounded bg-citation text-[0.6875rem] font-bold text-citation-foreground">
                    {source.n}
                  </span>
                  <span className="font-medium">{source.name}</span>
                  <span className="text-muted-foreground">in {source.section}</span>
                </li>
              ))}
            </ul>
          </div>
        </figure>
      </section>

      <section aria-labelledby="how-heading">
        <h2 id="how-heading" className="text-2xl font-semibold sm:text-3xl">
          How answers are built
        </h2>
        <div className="mt-8 grid gap-8 sm:grid-cols-3">
          {HOW_IT_WORKS.map(({ icon: Icon, title, text }) => (
            <div key={title}>
              <Icon className="size-5 text-primary" aria-hidden="true" />
              <h3 className="mt-3 text-lg font-semibold">{title}</h3>
              <p className="mt-1.5 text-sm text-muted-foreground">{text}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
