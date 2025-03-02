# Django Trademark Agent (Unofficial)

This was an experiment to build an AI Agent that can help answer common questions about Django's Trademark policy.

Please note: It's not official or legal advice.

## Usage

```shell
$ uv run agent.py "I'm working on an open source third party package, and I want to use django in the name of the package. Am I allowed to do that?"
Approval status: True

Answer: Yes, you are allowed to include 'django' in your package's name provided that your package is open source (released under an OSI-approved license) and you do
not imply that your package is officially endorsed by the Django Software Foundation or the Django Core team. This is considered nominative use, which is allowed under
our trademark policy.

Reasoning: According to the Django trademark FAQ, if you are the author or maintainer of a Django-related package and your library is released under an OSI-approved
open source license, you are free to use 'django' in your package name. The key point is that you should not create an impression that your package is official or
endorsed by the DSF. Ensure that any use of the Django trademark does not incorporate the official logo or color palette unless you have obtained the necessary
approval, and avoid any implication of ownership or official status.

Sections:
- Trademark FAQ: We're the author/maintainer of a Django-related package
- Django Trademark License Agreement (nominative use)
```
