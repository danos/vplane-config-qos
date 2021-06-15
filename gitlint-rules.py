# Copyright (c) 2019-2021, AT&T Intellectual Property. All rights reserved.
# SPDX-License-Identifier: LGPL-2.1-only

from gitlint.rules import CommitRule, RuleViolation


class ContainsJiraTicket(CommitRule):
    """ This rule will enforce that each commit contains a JIRA Ticket
    """

    # A rule MUST have a human friendly name
    name = "body-requires-jira-ticket"

    # A rule MUST have a *unique* id, we recommend starting with UC
    # (for User-defined Commit-rule).
    id = "UC1"

    def validate(self, commit):
        for line in commit.message.body:
            if line.startswith("VRVDR-") or line.startswith("DAN-"):
                return

        msg = "Body does not contain a jira ticket (no new line containing 'VRVDR-'or 'DAN-')"
        return [RuleViolation(self.id, msg, line_nr=1)]
