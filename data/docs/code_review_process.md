# Code Review Process

## Purpose

Code review ensures code quality, shares knowledge across the team, and catches
defects before they reach production. Every change to the main branch must be
reviewed before merging.

## Workflow

1. A developer opens a pull request against the main branch, describing the
   change, linking any related ticket, and noting how it was tested.
2. The pull request is automatically checked by continuous integration, which
   runs the test suite, linter, and type checker. A failing check blocks merge.
3. At least one other engineer reviews the pull request. Changes to shared
   infrastructure or security-sensitive code require two reviewers.
4. The reviewer leaves comments directly on the diff. The author addresses each
   comment, either by making a change or explaining why no change is needed.
5. Once all required reviewers approve and checks pass, the author merges the
   pull request using squash-and-merge to keep history readable.

## Review Standards

Reviewers evaluate correctness, readability, test coverage, and adherence to the
team's style guide. Reviewers are expected to respond to review requests within
one business day. Large pull requests (over roughly 400 changed lines) should be
split into smaller, independently reviewable changes whenever possible.

## Emergency Fixes

Production incidents may use an expedited review process: a single reviewer can
approve a fix, provided the change is small and scoped strictly to resolving the
incident. A full review is still required afterward via a follow-up pull request
if any shortcuts were taken.
