# Ethics and Responsible Use

## Product purpose

Conversation Success Coach helps a human operator notice observable
conversation patterns and consider a constructive next action. It is not a
persuasion engine, automated representative, diagnostic system, employee
ranking tool, or hidden participant profiler.

The ethical boundary is implemented in schemas, policy code, interface copy,
API responses, audit behavior, and tests.

## Human agency

Every suggestion:

- is optional;
- includes editable example language;
- includes rationale, evidence, confidence, and limitations;
- requires human review;
- is marked `delivery="manual_only"`; and
- is marked `can_auto_send=false`.

The package contains no endpoint or connector that sends a message. Copying a
draft does not authorize delivery and does not impersonate the operator.

## Prohibited optimization goals

### Covert manipulation

The coach will not help trick, guilt, secretly pressure, or manipulate someone.
It redirects to transparent, permission-based language with a genuine way to
decline.

### Protected-attribute inference or targeting

The coach will not infer or target race, ethnicity, religion, sex, gender, age,
disability, sexual orientation, nationality, or related protected traits. In
recruiting and moderation, it redirects to stated, documented, role- or
policy-relevant criteria applied consistently.

The lexical policy detects explicit requests; it is not a substitute for legal
review or a complete discrimination-control program.

### Mental-health diagnosis

The coach will not label a person bipolar, psychotic, narcissistic,
psychopathic, or otherwise diagnose mental health or personality. It may
describe observable communication or safety behavior and recommend qualified
support or escalation channels.

### Deceptive urgency or scarcity

The coach will not invent a deadline, pretend an offer expires, or describe a
false “last chance.” It encourages stating real constraints and distinguishing
confirmed facts from estimates.

### Dependency optimization

The coach will not optimize for keeping users, customers, candidates, or
members dependent or “hooked.” It encourages durable value, informed choice,
and easy disengagement.

### Impersonation and automatic sending

The coach will not impersonate a person or send automatically as them. Example
language is visibly labeled as a draft to adapt.

## Mode-specific responsibility

### Sales

Appropriate:

- answer pricing and feasibility questions;
- summarize the buyer's stated need;
- distinguish facts from estimates; and
- ask permission for a concrete next step.

Inappropriate:

- fabricated scarcity;
- exploiting fear or personal vulnerability;
- hiding material terms; and
- relentless pressure after a decline.

### Support

Appropriate:

- acknowledge stated impact;
- name the next diagnostic or remedy;
- assign ownership;
- give a realistic checkpoint; and
- offer an escalation path.

Inappropriate:

- claiming certainty without evidence;
- minimizing impact;
- exposing sensitive data in an ordinary channel; and
- treating ordinary coaching as sufficient for immediate safety concerns.

### Recruiting

Appropriate:

- consistent job-relevant process information;
- confirmed dates versus estimates;
- transparent evaluation steps; and
- an invitation for job-relevant questions or accommodation requests.

Inappropriate:

- inferred protected traits;
- diagnosis or personality labeling;
- undisclosed inconsistent standards; and
- coercive deadline claims.

### Community moderation

Appropriate:

- name observable behavior;
- cite the same published rule for everyone;
- request one concrete change;
- pause a thread when appropriate; and
- preserve review or appeal.

Inappropriate:

- identity-based assumptions;
- motive or diagnosis speculation;
- personalized humiliation; and
- inconsistent punishment designed to increase dependence or fear.

## Interpreting signals

Scores are directional summaries of visible language and turn structure.

They are not:

- truth;
- emotion detection;
- intent detection;
- a personality assessment;
- a protected-trait proxy;
- an employee performance score; or
- proof that a suggestion caused an outcome.

Confidence increases modestly with transcript length but remains bounded. Every
response includes limitations. Organization policy, cultural context, power
dynamics, irony, and events outside the transcript may change the correct
interpretation.

## Risk and escalation

Threat, harassment, trust-break, and sensitive-data patterns create visible
risk signals. They do not automatically punish a participant. The suggested
boundary is to pause ordinary coaching and follow an organization's established
safety, escalation, privacy, or moderation process.

The engine cannot determine whether a threat is credible or imminent.

## Data ethics

- Ad hoc analysis is stateless by default.
- Retention is explicit and bounded.
- Raw content requires an operator setting and request-level consent.
- Evidence excerpts redact several obvious direct-identifier shapes.
- Audit events exclude transcript and free-form note content.
- Purge is available by conversation and for all non-demo content.
- The fictional seed must never be replaced with real people or customer data
  in the public package.

Regex redaction is incomplete. Operators remain responsible for using approved
channels and data-handling procedures.

## Feedback ethics

Accepted/rejected feedback can improve playbook review. Outcome labels can show
directional movement. Neither should be used to:

- rank individual employees;
- create hidden worker profiles;
- infer protected traits;
- claim causal uplift from small samples; or
- suppress an operator's ability to reject a suggestion.

## Extending the system

Any new connector, model, scoring rule, mode, or delivery capability must
undergo review for:

- human-control impact;
- discrimination and proxy risk;
- manipulation risk;
- data minimization and retention;
- audit content;
- security boundary;
- failure and false-positive behavior; and
- tests that preserve current prohibitions.

Automatic sending or impersonation would be a fundamental product-boundary
change, not an ordinary feature addition.

