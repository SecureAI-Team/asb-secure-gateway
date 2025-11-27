package prompt

default allow = {"allow": true}

allow = {"allow": false, "reason": reason} {
    reasons := deny_reasons
    count(reasons) > 0
    reason := concat("; ", reasons)
}

deny_reasons[reason] {
    input.subject.user_id == "blocked"
    reason := "blocked user"
}

deny_reasons[reason] {
    t := input.context.metadata.temperature
    t > 1.0
    reason := "temperature too high"
}

deny_reasons[reason] {
    count := count(input.context.metadata.message_roles)
    count > 32
    reason := "too many messages"
}

