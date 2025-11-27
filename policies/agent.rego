package agent

default allow = {"allow": true}

allow = {"allow": false, "reason": reason} {
    reasons := deny_reasons
    count(reasons) > 0
    reason := concat("; ", reasons)
}

deny_reasons[reason] {
    input.resource.name == "http_get"
    reason := "network access disabled"
}

deny_reasons[reason] {
    input.subject.user_id == "suspended"
    reason := "subject suspended"
}

