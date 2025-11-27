package rag

default allow = {"allow": true}

allow = {"allow": false, "reason": reason} {
    reasons := deny_reasons
    count(reasons) > 0
    reason := concat("; ", reasons)
}

deny_reasons[reason] {
    input.context.metadata.top_k > 10
    reason := "top_k too large"
}

deny_reasons[reason] {
    input.context.metadata.query_length > 2000
    reason := "query too long"
}

