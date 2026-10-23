# Security policy

Please report vulnerabilities privately through GitHub's
[private vulnerability reporting](https://github.com/B0yko/cheat-index/security/advisories/new) for this
repository. Do not open a public issue.

In scope: anything that lets an agent container reach the OpenRouter key, the hidden checks, the host, or a network
host off the allow-list; the model gateway accepting a token from another run or after its run ended; the
verification container having network access; secrets or private paths ending up in results or release assets.

The project runs third-party agent CLIs with broad permissions inside containers. Run it only on a machine where
that is acceptable, and keep your OpenRouter key's spending limit low.
