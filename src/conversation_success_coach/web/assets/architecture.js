(() => {
    "use strict";

    const explorer = document.querySelector("[data-flow-explorer]");
    if (!explorer) {
        return;
    }

    const scenarios = {
        analysis: {
            title: "Analyze a conversation",
            summary: "Validated turns move through responsible-use checks, observable signal analysis, a mode adapter, and an explainable response.",
            steps: [
                {
                    lane: "Client",
                    laneClass: "client",
                    title: "Operator requests analysis",
                    short: "Mode, turns, context, and data controls",
                    copy: "The dashboard sends an explicit coaching mode, ordered conversation turns, optional context, and per-request persistence controls.",
                    proof: "POST /api/v1/analyze",
                },
                {
                    lane: "API service",
                    laneClass: "service",
                    title: "Contract validation",
                    short: "Strict schema and bounded inputs",
                    copy: "Pydantic rejects unknown fields, invalid modes, oversized turns, and inconsistent retention or consent combinations.",
                    proof: "AnalyzeRequest · extra='forbid'",
                },
                {
                    lane: "Coach engine",
                    laneClass: "engine",
                    title: "Responsible-use check",
                    short: "Unsafe objectives are redirected",
                    copy: "Explicit manipulation, protected-attribute inference, diagnosis, fake urgency, dependency, impersonation, or auto-send goals are converted into transparent alternatives.",
                    proof: "ResponsibleUse.behavior = standard | redirected",
                },
                {
                    lane: "Coach engine",
                    laneClass: "engine",
                    title: "Observable signal analysis",
                    short: "Momentum, tone, clarity, empathy, risk",
                    copy: "Deterministic analyzers score visible language and turn structure, redact evidence excerpts, and identify open questions and escalation signals.",
                    proof: "SHA-256 canonical input fingerprint",
                },
                {
                    lane: "Coach engine",
                    laneClass: "engine",
                    title: "Mode-aware next action",
                    short: "Sales, support, recruiting, or community",
                    copy: "The selected mode changes the recommended next-step pattern while the same hard responsible-use boundaries remain in force.",
                    proof: "Suggestion.delivery = manual_only",
                },
                {
                    lane: "Client",
                    laneClass: "client",
                    title: "Human review",
                    short: "Evidence, confidence, limits, editable draft",
                    copy: "The response explains why each action was proposed and requires the operator to accept, reject, edit, or ignore it. No delivery transport exists.",
                    proof: "can_auto_send = false",
                },
            ],
        },
        feedback: {
            title: "Record feedback and outcomes",
            summary: "Operator decisions become directional product evidence without claiming that a suggestion caused the result.",
            steps: [
                {
                    lane: "Client",
                    laneClass: "client",
                    title: "Operator makes a decision",
                    short: "Accept, reject, or record an outcome",
                    copy: "Feedback is explicit and separate from message delivery. The operator can reject a suggestion without penalty or suppressing future human choice.",
                    proof: "accepted | rejected | outcome",
                },
                {
                    lane: "API service",
                    laneClass: "service",
                    title: "Feedback validation",
                    short: "References and outcome fields are checked",
                    copy: "Accepted or rejected feedback requires a real suggestion. Outcome feedback requires a conversation and a neutral outcome enum.",
                    proof: "POST /api/v1/feedback",
                },
                {
                    lane: "State",
                    laneClass: "store",
                    title: "Local feedback record",
                    short: "SQLite stores the selected state",
                    copy: "The repository records the decision, updates suggestion status, and keeps free-form notes out of the audit event.",
                    proof: "feedback + suggestions tables",
                },
                {
                    lane: "State",
                    laneClass: "store",
                    title: "Content-free audit",
                    short: "Metadata, not transcript or note text",
                    copy: "The audit trail records event type, resource ids, outcome metadata, and whether a note exists—not the note or conversation content.",
                    proof: "note_in_audit = false",
                },
                {
                    lane: "API service",
                    laneClass: "service",
                    title: "Metrics aggregation",
                    short: "Adoption, outcomes, and signal averages",
                    copy: "Metrics calculate acceptance and outcome counts with explicit limitations: small samples are directional and do not establish causality.",
                    proof: "GET /api/v1/metrics",
                },
                {
                    lane: "Client",
                    laneClass: "client",
                    title: "Operator learns, not ranks",
                    short: "Use trends to improve playbooks",
                    copy: "The dashboard presents team-level coaching signals and avoids employee scoring, protected-trait segmentation, or hidden performance profiles.",
                    proof: "limitations[] included in metrics",
                },
            ],
        },
        privacy: {
            title: "Apply the privacy lifecycle",
            summary: "Stateless is the default. Retention requires explicit intent, bounded time, and—when raw content is stored—confirmed consent.",
            steps: [
                {
                    lane: "Client",
                    laneClass: "client",
                    title: "Choose data handling",
                    short: "Default: analyze without persistence",
                    copy: "Each request declares whether analysis should be retained, whether raw content may be stored, and the requested retention period.",
                    proof: "persist_analysis = false by default",
                },
                {
                    lane: "API service",
                    laneClass: "service",
                    title: "Enforce consistent controls",
                    short: "Persistence, consent, and TTL must agree",
                    copy: "A persisted analysis needs a 1–30 day period. Raw content additionally requires confirmed consent and the operator-level raw-storage switch.",
                    proof: "409 privacy_policy_conflict on mismatch",
                },
                {
                    lane: "Coach engine",
                    laneClass: "engine",
                    title: "Redact evidence excerpts",
                    short: "Common identifiers are removed",
                    copy: "Evidence snippets redact email, phone, payment-number, government-id, and long-number shapes before entering an explanation.",
                    proof: "redact_evidence()",
                },
                {
                    lane: "State",
                    laneClass: "store",
                    title: "Store the minimum",
                    short: "Derived result or consented transcript",
                    copy: "Stateless results are returned and discarded. Persisted analyses carry an expiry. New raw transcript workspaces also carry their own expiry.",
                    proof: "analyses.expires_at · conversations.expires_at",
                },
                {
                    lane: "State",
                    laneClass: "store",
                    title: "Purge expired content",
                    short: "Delete non-demo records at or before TTL",
                    copy: "The retention endpoint deletes expired analyses, conversations, and audit entries older than the configured audit window.",
                    proof: "POST /api/v1/privacy/retention/run",
                },
                {
                    lane: "Client",
                    laneClass: "client",
                    title: "Receive a deletion receipt",
                    short: "Counts and scope, no deleted content",
                    copy: "The response and audit record state what class of records was removed while deliberately excluding transcript text.",
                    proof: "audit_contains_transcript_text = false",
                },
            ],
        },
        reset: {
            title: "Reset the fictional demo",
            summary: "One endpoint clears mutable local state and restores the canonical scenarios, analyses, playbooks, feedback, and audit baseline.",
            steps: [
                {
                    lane: "Client",
                    laneClass: "client",
                    title: "Operator confirms reset",
                    short: "A visible, deliberate demo action",
                    copy: "The dashboard asks for confirmation because reset overwrites mutable demo state. It never touches any directory outside the product database.",
                    proof: "POST /api/v1/demo/reset",
                },
                {
                    lane: "API service",
                    laneClass: "service",
                    title: "Begin local reset",
                    short: "One repository boundary",
                    copy: "The application service invokes the seed routine against the configured SQLite database. No external service or credential is involved.",
                    proof: "seed_demo(reset=true)",
                },
                {
                    lane: "State",
                    laneClass: "store",
                    title: "Clear mutable records",
                    short: "Delete in foreign-key-safe order",
                    copy: "Feedback, suggestions, analyses, turns, conversations, playbooks, audit, and seed metadata are removed in a transaction.",
                    proof: "Repository.clear_all()",
                },
                {
                    lane: "State",
                    laneClass: "store",
                    title: "Restore fictional scenarios",
                    short: "Four modes, four playbooks",
                    copy: "Canonical fictional names, turns, goals, and mode-specific playbooks are inserted with no copied secrets, customer data, or generated binaries.",
                    proof: "SEED_VERSION = 2026-08-30.1",
                },
                {
                    lane: "Coach engine",
                    laneClass: "engine",
                    title: "Recompute deterministic analysis",
                    short: "Seed metrics come from the real engine",
                    copy: "Each scenario is analyzed through the same engine used by the live endpoint, then seeded feedback and outcomes make the overview meeting-ready.",
                    proof: "ConversationAnalyzer.analyze()",
                },
                {
                    lane: "Client",
                    laneClass: "client",
                    title: "Reload the workspace",
                    short: "Known state, ready for another walkthrough",
                    copy: "The dashboard refreshes conversations, metrics, playbooks, privacy settings, and audit history from the restored API state.",
                    proof: "4 conversations · 4 playbooks",
                },
            ],
        },
    };

    const canvas = explorer.querySelector("[data-flow-canvas]");
    const title = explorer.querySelector("[data-flow-title]");
    const summary = explorer.querySelector("[data-flow-summary]");
    const status = explorer.querySelector("[data-flow-status]");
    const playButton = explorer.querySelector("[data-flow-play]");
    const resetButton = explorer.querySelector("[data-flow-reset]");
    const detailStep = explorer.querySelector("[data-flow-detail-step]");
    const detailLane = explorer.querySelector("[data-flow-detail-lane]");
    const detailTitle = explorer.querySelector("[data-flow-detail-title]");
    const detailCopy = explorer.querySelector("[data-flow-detail-copy]");
    const detailProof = explorer.querySelector("[data-flow-detail-proof]");
    const tabs = Array.from(explorer.querySelectorAll("[data-flow-scenario]"));

    let scenarioKey = "analysis";
    let stepIndex = 0;
    let timer = null;

    const playIcon = '<svg viewBox="0 0 20 20" fill="none"><path d="m7 5 7 5-7 5z" fill="currentColor"/></svg>';
    const pauseIcon = '<svg viewBox="0 0 20 20" fill="none"><path d="M7 5v10M13 5v10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>';

    const stop = () => {
        if (timer) {
            window.clearInterval(timer);
            timer = null;
        }
        playButton.innerHTML = playIcon;
        playButton.setAttribute("aria-label", "Play journey");
    };

    const updateDetail = () => {
        const scenario = scenarios[scenarioKey];
        const step = scenario.steps[stepIndex];
        detailStep.textContent = `Step ${stepIndex + 1}`;
        detailLane.textContent = step.lane;
        detailTitle.textContent = step.title;
        detailCopy.textContent = step.copy;
        detailProof.textContent = step.proof;
        status.textContent = `Step ${stepIndex + 1} / ${scenario.steps.length}`;
        const nodes = Array.from(canvas.querySelectorAll(".flow-node"));
        const connectors = Array.from(canvas.querySelectorAll(".flow-connector"));
        nodes.forEach((node, index) => {
            node.classList.toggle("active", index === stepIndex);
            node.classList.toggle("complete", index < stepIndex);
            node.setAttribute("aria-current", index === stepIndex ? "step" : "false");
        });
        connectors.forEach((connector, index) => {
            connector.classList.toggle("active", index === stepIndex - 1);
        });
        const activeNode = nodes[stepIndex];
        const scrollViewport = canvas.closest(".flow-canvas-scroll");
        if (activeNode && scrollViewport) {
            const centeredLeft =
                activeNode.offsetLeft -
                (scrollViewport.clientWidth - activeNode.offsetWidth) / 2;
            scrollViewport.scrollTo({
                behavior: "smooth",
                left: Math.max(0, centeredLeft),
            });
        }
    };

    const render = () => {
        const scenario = scenarios[scenarioKey];
        title.textContent = scenario.title;
        summary.textContent = scenario.summary;
        canvas.replaceChildren();
        scenario.steps.forEach((step, index) => {
            const node = document.createElement("button");
            node.type = "button";
            node.className = "flow-node";
            node.innerHTML = `
                <span class="flow-node-lane ${step.laneClass}">${step.lane}</span>
                <strong>${step.title}</strong>
                <small>${step.short}</small>
            `;
            node.addEventListener("click", () => {
                stop();
                stepIndex = index;
                updateDetail();
            });
            canvas.appendChild(node);
            if (index < scenario.steps.length - 1) {
                const connector = document.createElement("span");
                connector.className = "flow-connector";
                connector.textContent = "→";
                connector.setAttribute("aria-hidden", "true");
                canvas.appendChild(connector);
            }
        });
        updateDetail();
    };

    const play = () => {
        if (timer) {
            stop();
            return;
        }
        playButton.innerHTML = pauseIcon;
        playButton.setAttribute("aria-label", "Pause journey");
        timer = window.setInterval(() => {
            const length = scenarios[scenarioKey].steps.length;
            if (stepIndex >= length - 1) {
                stop();
                return;
            }
            stepIndex += 1;
            updateDetail();
        }, 1450);
    };

    tabs.forEach((tab) => {
        tab.addEventListener("click", () => {
            stop();
            scenarioKey = tab.dataset.flowScenario;
            stepIndex = 0;
            tabs.forEach((candidate) => {
                const active = candidate === tab;
                candidate.classList.toggle("active", active);
                candidate.setAttribute("aria-selected", String(active));
            });
            render();
        });
    });
    playButton.addEventListener("click", play);
    resetButton.addEventListener("click", () => {
        stop();
        stepIndex = 0;
        updateDetail();
    });

    render();
})();
