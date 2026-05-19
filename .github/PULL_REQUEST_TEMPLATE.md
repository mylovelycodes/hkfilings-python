<!-- Thanks for the PR! Please fill out the following so we can review quickly. -->

## What

<!-- One-paragraph summary of the change. -->

## Why

<!-- The user-facing reason, not just the implementation reason.
     Link the issue: Closes #123 -->

## Compatibility

- [ ] No breaking changes to public methods or types
- [ ] If a public method gained a parameter, it's keyword-only with a default
- [ ] If a dataclass gained a field, it has a sensible default (so existing code
      that constructs it positionally keeps working)

## Quality gates

- [ ] `pytest` passes locally
- [ ] `ruff check .` is clean
- [ ] `mypy hkfilings` is clean
- [ ] Coverage didn't drop below 85%
- [ ] `CHANGELOG.md` updated under `[Unreleased]`

## Notes for reviewer

<!-- Anything tricky to look at? Anything you'd appreciate a second opinion on? -->
