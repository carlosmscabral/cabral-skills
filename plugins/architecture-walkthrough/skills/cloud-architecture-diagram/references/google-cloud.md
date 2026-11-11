# Google Cloud semantics

Consult current product documentation when behavior matters. Reference
architectures are examples, not proof of the user's deployment. Start at the
[Architecture Center](https://cloud.google.com/architecture) and
[Well-Architected Framework](https://cloud.google.com/architecture/framework).

| Boundary | Establish before drawing |
| --- | --- |
| Organization / folder / project | Ownership, not a network perimeter |
| Region / zone | Actual location; one service's region does not locate the entire app |
| VPC / subnet | Actual placement/connectivity; regional subnet versus VPC |
| Trust / exposure | Who can call what, authentication and ingress |
| Functional group | A concern such as data or operations, not a deployment claim |

Managed services are not automatically inside the application's subnet. A private
bucket does not imply VPC containment; Cloud Run VPC egress does not turn the
service into a VM in that subnet. Draw verified connectivity and label its
mechanism. Unknown location stays unspecified. Nest only true containment.

## Trace requests and events

Record source, destination, operation/payload, transport/delivery type and identity
when known. Distinguish user authentication, workload identity and authorization.
Show load balancers, IAP, gateways and private endpoints only with evidence or as
explicit proposals.

For Pub/Sub, distinguish topics and subscriptions; establish push versus pull
before drawing who initiates delivery. Show acknowledgment, retry ownership,
idempotency and dead-letter destination when relevant and verified or explicitly
proposed. A queue does not imply exactly-once processing. Separate request replies
from background work. Define line styles with a legend: dashed cannot silently
mean both asynchronous delivery and secondary operations. Numbering is independent.

## Completeness without clutter

Review entry/authentication, service roles, significant scaling limits, durable
data/retention, timeouts/backpressure/recovery, telemetry/operator action, and
build/deploy paths. Draw only concerns relevant to the audience and supported by
evidence. Keep unsupported controls in assumptions/proposals notes. Distinguish
current and target state. Every numeric claim needs a source, units and relevant
time window. Never transfer sample numbers into a real app as defaults.
