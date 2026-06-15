"""Query CloudWatch for Bedrock invocation latency metrics.

AWS auto-captures latency on every Bedrock call as a CloudWatch metric named
'InvocationLatency'. This script pulls the last hour's worth and prints
basic statistics — proves we have server-side latency measurement available
rather than relying solely on Python local timing.
"""
import boto3
from datetime import datetime, timedelta, timezone

REGION = "us-east-1"
MODEL_ID = "us.meta.llama3-1-8b-instruct-v1:0"

client = boto3.client("cloudwatch", region_name=REGION)

# Look at the last hour of metrics
end_time = datetime.now(timezone.utc)
start_time = end_time - timedelta(hours=1)

print(f"Querying CloudWatch metric 'InvocationLatency' for Bedrock")
print(f"Region:     {REGION}")
print(f"Model ID:   {MODEL_ID}")
print(f"Time range: {start_time.isoformat()}  to  {end_time.isoformat()}")
print()

response = client.get_metric_statistics(
    Namespace="AWS/Bedrock",
    MetricName="InvocationLatency",
    Dimensions=[{"Name": "ModelId", "Value": MODEL_ID}],
    StartTime=start_time,
    EndTime=end_time,
    Period=300,  # 5-minute buckets
    Statistics=["Average", "Minimum", "Maximum", "SampleCount"],
)

datapoints = sorted(response.get("Datapoints", []), key=lambda d: d["Timestamp"])

if not datapoints:
    print("No datapoints found. (Either no invocations in the last hour,")
    print("or CloudWatch hasn't propagated them yet — metrics can lag by 2-5 min.)")
else:
    print(f"Found {len(datapoints)} 5-minute buckets with invocations:\n")
    print(f"{'Timestamp':<30} {'Calls':>6} {'Min ms':>9} {'Avg ms':>9} {'Max ms':>9}")
    print("-" * 65)
    total_calls = 0
    all_avgs = []
    for d in datapoints:
        ts = d["Timestamp"].strftime("%Y-%m-%d %H:%M:%S UTC")
        n = int(d["SampleCount"])
        mn = d["Minimum"]
        av = d["Average"]
        mx = d["Maximum"]
        total_calls += n
        all_avgs.append(av)
        print(f"{ts:<30} {n:>6} {mn:>9.1f} {av:>9.1f} {mx:>9.1f}")
    print()
    print(f"Total invocations: {total_calls}")
    print(f"Overall mean latency: {sum(all_avgs)/len(all_avgs):.1f} ms")