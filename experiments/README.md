# Experiments

Tests of the detector's own behaviour, published whichever way they land.

`examples/` holds reports the tool wrote about other people's content. This folder holds what
happens when it's pointed at itself: does a prompt change help, how much does a verdict move
between runs, what does it miss. Null and negative results belong here as much as positive ones —
a fact-checking tool that only publishes its wins has the problem it exists to detect.

| Date | Experiment | Result |
|---|---|---|
| 2026-07-30 | [Does telling it to "use credible sources" help?](./2026-07-30-credible-sources.md) | Inconclusive by design failure — run-to-run noise exceeds the effect. Found instead that most high-reputation news outlets are unreachable to the agent's crawler, and their reporting re-enters laundered through aggregators. |
| 2026-07-30 | [Can a search API reach the sources a crawler can't?](./2026-07-30-search-api-access.md) | Yes, 13 of 16 blocked domains return usable article text through Tavily. Not adopting it: their crawler reaches those sources by not advertising a user agent, which is the same circumvention refused directly. |
