# Can a search API reach the sources a crawler can't?

**Run:** 2026-07-30 · **Tool version:** v0.5.1 · **Follows:** [the credible-sources experiment](./2026-07-30-credible-sources.md)

The earlier experiment found that 16 of the news organisations with the strongest fact-checking reputations refuse this agent's crawler. That left an obvious question I could not answer at the time: is that a property of crawlers in general, or just of *this* crawler?

Search APIs like Tavily, Serper and Exa keep their own indexes. If those indexes contain Reuters and the New York Times, then the blocklist is an architecture problem with a fix, and the fix is to stop crawling and start querying an index.

So I tested it. Short version: **the content is reachable, and I decided not to use it anyway.**

---

## What I ran

Tavily, free tier, one API key. For each of the 16 domains blocked to the crawler, a query restricted to that domain with `include_raw_content: true`. Control group of four domains the crawler can already reach.

## First pass, which was wrong

Every one of the 16 returned results. All of them had text in the `content` field. I wrote down "16/16" and nearly stopped there.

That number was measuring the wrong thing. The default `content` field is a snippet of about 150 characters, roughly what you would get from a search engine result page. You cannot verify a claim from 150 characters. It tells you an article exists, not what it says.

Worth stating plainly, because it is the same mistake this tool exists to catch: the first result looked decisive, and it was decisive about nothing.

## Second pass, measuring usable text

Same 16 domains, but this time measuring the length of actual article prose in `raw_content`, with markdown link syntax stripped, and excluding advertorials.

**13 of 16 return usable article text.** Reuters, AP, NYT, Economist, Atlantic, Politico, Wired, The Verge, Ars Technica, BBC, Business Insider, ZDNet and FT all came back with real article bodies, several over 10,000 characters of prose. Ars Technica returned 48,000.

Three did not:

| Domain | Prose | What came back |
|---|---|---|
| wsj.com | 1,295 chars | Dow Jones reprints boilerplate, not the article |
| newyorker.com | 1,366 chars | Paywall stub |
| theguardian.com | 1,926 chars | Short piece, possibly genuine |

Two other things worth recording. The FT result on the first pass was `/partnercontent/comarch/`, which is paid advertorial the FT serves to everyone, not journalism. And on one run, `include_domains: ["nytimes.com"]` returned a result from dictionary.com, so the domain filter is not reliable.

## So how is it getting Reuters?

This is the part that mattered.

It is not licensing. It is not a rack of browsers with paid subscriptions either, and the paywall results are the proof: if Tavily had a WSJ subscription, WSJ would not come back as reprints boilerplate.

The `raw_content` is a fetched web page converted to markdown. It contains "Skip to main content", cookie banners, the word "advertisement", and ad tracking parameters (`us_privacy=1---`, `tagmgr=gtm`) still stuck to the end. That is not a clean content feed from a partner. That is somebody loading the page.

Their own [crawler documentation](https://docs.tavily.com/documentation/search-crawler) explains the rest:

> "The Tavily Search crawler does not advertise a differentiated user agent because we must avoid discrimination from websites that allow only Google to crawl them."

> "If a domain or page is not crawlable by Googlebot, then Tavily Search's bot will not crawl it either."

That is the whole mechanism. Publishers block `ClaudeBot` and `GPTBot` by name in robots.txt, because they do not want AI crawlers. They keep allowing `Googlebot`, because they still want search traffic. Tavily does not say who it is, so it gets Googlebot's permissions.

## Why I'm not adopting it

Earlier the same day, someone asked me whether the tool could just identify as something other than an agent to get past those blocks. I said no. Dressing a script up as a browser to walk through a door a publisher closed is circumvention, whatever the user-agent string says, and a fact-checker caught doing it has a much bigger problem than a missing source.

Routing through a search API reaches the same result with one more layer in between. The reason it can read Reuters is that it does not say who it is.

To be fair to Tavily: this is legal, it respects Googlebot's robots.txt, it is standard practice across AI search, and plenty of serious products are built on it. They also document it openly, which is more than most. This is not an accusation.

But publishers who allow Googlebot and block AI crawlers by name have said something specific, and this walks through the gap between those two rules. For a tool whose entire argument is "check it yourself", "my vendor does it" is not a distinction I want to defend.

So the honest answer to the question I set out to test: **yes, a search API reaches the blocked sources, and no, I'm not going to use it for that.**

## What I'm doing instead

Unchanged from the last experiment, and now better justified:

- **Publisher APIs where they exist.** The Guardian's Open Platform is free, gives full article body, and is offered deliberately. That is a door somebody opened.
- **Wikipedia as a citation index.** Reachable, and its reference lists point straight at the reporting I can't fetch, with claim, date and outlet.
- **Dedicated fact-checkers.** All reachable, and built for exactly this.
- **Primary sources.** Already ranked above reporting in [RUBRIC.md](../skills/analysis/bullshit-detector/RUBRIC.md), and reachable.

## Limits

- One provider, one day, 16 domains, one query per domain. Serper and Exa may behave differently and I have not tested them.
- "Usable" here means more than 3,000 characters of prose on the right domain and not an advertorial. That is a crude threshold, not a quality judgement. Long does not mean true.
- The Guardian result may be a genuinely short article rather than a stub. I did not check it by hand.
- Tavily's behaviour could change. The documentation quoted above was live on 2026-07-30.

## Reproducing this

The blocklist half is still the cheap part: restrict a search to `reuters.com` with your agent's own web search and read the error. For this half you need a Tavily key, and the whole test is one request per domain with `include_raw_content: true`. Measure the prose length, not whether results came back. That was my mistake and it is an easy one to repeat.
