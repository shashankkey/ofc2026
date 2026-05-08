# Aternity Kibana Dashboards — Complete Guide

> **Data Stream:** `metrics-aternity.business_activities-default`
>
> **Elasticsearch:** 8.17.2 | **Auth:** Basic

All visualizations below use the data stream index pattern. In Kibana, create a **Data View** pointing to `metrics-aternity.business_activities-*` before building these.

---

## How to Set Up

1. Go to **Stack Management → Data Views** (formerly Index Patterns)
2. Click **Create data view**
3. Set:
   - **Name:** `Aternity Business Activities`
   - **Index pattern:** `metrics-aternity.business_activities-*`
   - **Timestamp field:** `@timestamp`
4. Save → Go to **Dashboard → Create dashboard**

---

## Dashboard 1: Aternity Executive Overview

> **Purpose:** Single-pane-of-glass for leadership/IT managers. Shows overall activity health at a glance.

### Panel 1.1 — Total Activities Performed

| Setting | Value |
|---|---|
| **Title** | Total Activities Performed |
| **Description** | Total number of business activities executed across all applications, users, and devices in the selected time range. |
| **Visualization Type** | Metric |
| **Configuration** | |
| Metric aggregation | `Sum` of `volume` |
| Font size | Large |
| Format | Number with comma separator |

---

### Panel 1.2 — Average Response Time (ms)

| Setting | Value |
|---|---|
| **Title** | Avg Activity Response Time |
| **Description** | Global average response time across all monitored business activities. A rising number indicates degrading user experience. |
| **Visualization Type** | Metric |
| **Configuration** | |
| Metric aggregation | `Average` of `activity_response_avg` |
| Format | Number, suffix: ` ms` |
| Color rules | Green < 3000, Yellow 3000–5000, Red > 5000 |

---

### Panel 1.3 — Activity Volume Over Time

| Setting | Value |
|---|---|
| **Title** | Activity Volume Over Time |
| **Description** | Time-series trend of total activity executions. Sudden drops may indicate outages; spikes may indicate batch processing or unusual usage. |
| **Visualization Type** | Area Chart |
| **Configuration** | |
| X-axis | `@timestamp` (Date Histogram, auto interval) |
| Y-axis | `Sum` of `volume` |
| Split series | None (single line) |

---

### Panel 1.4 — Response Time Trend

| Setting | Value |
|---|---|
| **Title** | Response Time Trend |
| **Description** | Hourly trend of average activity response time. Use to identify performance degradation over time or correlate with change windows. |
| **Visualization Type** | Line Chart |
| **Configuration** | |
| X-axis | `@timestamp` (Date Histogram, auto interval) |
| Y-axis | `Average` of `activity_response_avg` |
| Reference line | Add horizontal line at 5000 ms (SLA threshold) |

---

### Panel 1.5 — Top 10 Most Used Applications

| Setting | Value |
|---|---|
| **Title** | Top 10 Most Used Applications |
| **Description** | Applications ranked by total activity volume. Shows where your users spend the most time and which apps have the highest business impact. |
| **Visualization Type** | Horizontal Bar Chart |
| **Configuration** | |
| X-axis | `Sum` of `volume` |
| Y-axis | `application_name.keyword` (Top 10 by Sum of volume) |
| Sort | Descending by volume |

---

### Panel 1.6 — Top 10 Slowest Applications

| Setting | Value |
|---|---|
| **Title** | Top 10 Slowest Applications |
| **Description** | Applications with the highest average response time. These are the apps causing the most user frustration and should be prioritized for optimization. |
| **Visualization Type** | Horizontal Bar Chart |
| **Configuration** | |
| X-axis | `Average` of `activity_response_avg` |
| Y-axis | `application_name.keyword` (Top 10 by Avg response) |
| Color | Red gradient |

---

### Panel 1.7 — Activity Volume by Application (Proportion)

| Setting | Value |
|---|---|
| **Title** | Activity Distribution by Application |
| **Description** | Proportional view of activity volume across applications. Identifies which applications dominate your enterprise workload. |
| **Visualization Type** | Donut / Pie Chart |
| **Configuration** | |
| Slice by | `application_name.keyword` (Top 10) |
| Size by | `Sum` of `volume` |

---

### Panel 1.8 — Unique Users and Devices

| Setting | Value |
|---|---|
| **Title** | Unique Users & Devices |
| **Description** | Count of distinct users and devices that performed activities. Useful to understand the scope of your monitoring coverage. |
| **Visualization Type** | Metric (two metrics side by side) |
| **Configuration** | |
| Metric 1 | `Unique Count` of `username.keyword` → label: "Unique Users" |
| Metric 2 | `Unique Count` of `device_name.keyword` → label: "Unique Devices" |

---

## Dashboard 2: Application Performance Deep Dive

> **Purpose:** Detailed per-application analysis with response time breakdowns. The most actionable dashboard for IT operations.

### Panel 2.1 — Application Performance Table

| Setting | Value |
|---|---|
| **Title** | Application Performance Summary |
| **Description** | Sortable table showing every monitored application with its average, min, and max response times plus total activity volume. Sort by response time to find problem apps. |
| **Visualization Type** | Data Table (Lens) |
| **Configuration** | |
| Row (Bucket) | `application_name.keyword` (Top 25) |
| Metric columns | `Avg(activity_response_avg)`, `Max(activity_response_max)`, `Min(activity_response_min)`, `Sum(volume)` |
| Sort | Default: descending by Avg response |
| Column labels | "App Name", "Avg Resp (ms)", "Max Resp (ms)", "Min Resp (ms)", "Total Volume" |

---

### Panel 2.2 — Response Time Breakdown by Application

| Setting | Value |
|---|---|
| **Title** | Response Time Breakdown: Client vs Network vs Backend |
| **Description** | **The most important visualization.** Stacked bar showing where time is spent for each application. If the bar is mostly blue (client), the issue is device-side. Orange (network) = WAN/VPN issue. Purple (backend) = server-side issue. |
| **Visualization Type** | Horizontal Stacked Bar Chart |
| **Configuration** | |
| Y-axis | `application_name.keyword` (Top 15) |
| X-axis (stacked layers) | |
| Layer 1 | `Avg` of `activity_client_time_avg` → label: "Client Time", color: `#3498db` (blue) |
| Layer 2 | `Avg` of `activity_network_time_avg` → label: "Network Time", color: `#e67e22` (orange) |
| Layer 3 | `Avg` of `activity_backend_time_avg` → label: "Backend Time", color: `#9b59b6` (purple) |

> [!TIP]
> **How to read this chart:**
> - 🔵 **Mostly Blue (Client Time)** → User's device is slow — check CPU, RAM, disk
> - 🟠 **Mostly Orange (Network Time)** → Network latency — check VPN, WAN, WiFi
> - 🟣 **Mostly Purple (Backend Time)** → Server is slow — check app server, database

---

### Panel 2.3 — Activity Heat Map

| Setting | Value |
|---|---|
| **Title** | Activity Response Time Heat Map |
| **Description** | Heat map of response times across applications and activities. Dark red cells indicate the specific app+activity combinations suffering the worst performance. |
| **Visualization Type** | Heat Map (Lens) |
| **Configuration** | |
| X-axis | `activity_name.keyword` (Top 20) |
| Y-axis | `application_name.keyword` (Top 15) |
| Cell value | `Average` of `activity_response_avg` |
| Color palette | Green → Yellow → Red |

---

### Panel 2.4 — Response Time Distribution

| Setting | Value |
|---|---|
| **Title** | Response Time Distribution |
| **Description** | Histogram showing the distribution of response times. A healthy system shows most values clustered at the left (fast). A long right tail indicates outliers needing investigation. |
| **Visualization Type** | Histogram |
| **Configuration** | |
| Field | `activity_response_avg` |
| Bucket size | 500 ms |
| X-axis label | Response Time (ms) |
| Y-axis label | Count |

---

### Panel 2.5 — Per-Application Response Time Trend

| Setting | Value |
|---|---|
| **Title** | Response Time Trend by Application |
| **Description** | Multi-line time series showing response time trends for the top applications. Use to spot which apps are degrading and when the degradation started. |
| **Visualization Type** | Line Chart |
| **Configuration** | |
| X-axis | `@timestamp` (Date Histogram) |
| Y-axis | `Average` of `activity_response_avg` |
| Break down by | `application_name.keyword` (Top 5) |

---

## Dashboard 3: Location Performance Analysis

> **Purpose:** Identify offices, cities, or regions with poor application performance. Critical for remote/hybrid workforce monitoring.

### Panel 3.1 — Response Time by Location

| Setting | Value |
|---|---|
| **Title** | Avg Response Time by City |
| **Description** | Bar chart showing average activity response time per city. High values indicate network or infrastructure issues at specific locations. |
| **Visualization Type** | Horizontal Bar Chart |
| **Configuration** | |
| Y-axis | `location_city.keyword` (Top 20) |
| X-axis | `Average` of `activity_response_avg` |
| Sort | Descending by average response |

---

### Panel 3.2 — Network Time by Location

| Setting | Value |
|---|---|
| **Title** | Network Latency by Location |
| **Description** | Average network time per city. High network time at specific locations often points to WAN link saturation, VPN bottlenecks, or poor WiFi infrastructure. |
| **Visualization Type** | Horizontal Bar Chart |
| **Configuration** | |
| Y-axis | `location_city.keyword` (Top 20) |
| X-axis | `Average` of `activity_network_time_avg` |
| Color | Orange |

---

### Panel 3.3 — Volume by Country

| Setting | Value |
|---|---|
| **Title** | Activity Volume by Country |
| **Description** | Geographic distribution of activity volume. Shows where your user base is concentrated and helps with capacity planning per region. |
| **Visualization Type** | Pie Chart |
| **Configuration** | |
| Slice by | `location_country.keyword` (Top 15) |
| Size by | `Sum` of `volume` |

---

### Panel 3.4 — Location vs Application Performance

| Setting | Value |
|---|---|
| **Title** | Location × Application Performance |
| **Description** | Table cross-referencing locations with applications to identify if a specific app is slow everywhere or only in certain locations. |
| **Visualization Type** | Data Table |
| **Configuration** | |
| Row 1 (Bucket) | `location_city.keyword` (Top 10) |
| Row 2 (Sub-bucket) | `application_name.keyword` (Top 5) |
| Metrics | `Avg(activity_response_avg)`, `Sum(volume)` |

---

## Dashboard 4: User Experience Analysis

> **Purpose:** Identify users who are suffering the worst digital experience. Essential for help desk prioritization and proactive support.

### Panel 4.1 — Most Impacted Users

| Setting | Value |
|---|---|
| **Title** | Top 20 Most Impacted Users |
| **Description** | Users experiencing the highest average response times. These users should be proactively contacted by IT support before they raise tickets. |
| **Visualization Type** | Data Table |
| **Configuration** | |
| Row (Bucket) | `username.keyword` (Top 20, ordered by Avg response descending) |
| Metrics | `Avg(activity_response_avg)`, `Max(activity_response_max)`, `Sum(volume)` |
| Column labels | "User", "Avg Response (ms)", "Worst Response (ms)", "Activity Count" |

---

### Panel 4.2 — Power Users (Highest Volume)

| Setting | Value |
|---|---|
| **Title** | Power Users — Highest Activity Volume |
| **Description** | Users with the most activity executions. These are your heavy users — their experience has the highest business impact. |
| **Visualization Type** | Horizontal Bar Chart |
| **Configuration** | |
| Y-axis | `username.keyword` (Top 15) |
| X-axis | `Sum` of `volume` |

---

### Panel 4.3 — User Count by Department

| Setting | Value |
|---|---|
| **Title** | Active Users by Department |
| **Description** | Number of unique active users per department. Helps identify which business units are most dependent on monitored applications. |
| **Visualization Type** | Pie Chart |
| **Configuration** | |
| Slice by | `department.keyword` (Top 15) |
| Size by | `Unique Count` of `username.keyword` |

---

### Panel 4.4 — Department Response Time Comparison

| Setting | Value |
|---|---|
| **Title** | Avg Response Time by Department |
| **Description** | Compare application performance across departments. If Finance has slower times than HR, it may indicate specific app issues or infrastructure differences. |
| **Visualization Type** | Bar Chart |
| **Configuration** | |
| X-axis | `department.keyword` (Top 10) |
| Y-axis | `Average` of `activity_response_avg` |

---

## Dashboard 5: Device & OS Analysis

> **Purpose:** Understand how device hardware and OS affect application performance. Supports hardware refresh and OS migration decisions.

### Panel 5.1 — Response Time by Device Type

| Setting | Value |
|---|---|
| **Title** | Response Time by Device Type |
| **Description** | Compare average response times across Laptops, Desktops, and VDI. If VDI shows significantly worse times, the virtual infrastructure may need optimization. |
| **Visualization Type** | Bar Chart |
| **Configuration** | |
| X-axis | `device_type.keyword` |
| Y-axis | `Average` of `activity_response_avg` |

---

### Panel 5.2 — Response Time by OS

| Setting | Value |
|---|---|
| **Title** | Response Time by Operating System |
| **Description** | Compare app performance across OS versions. Useful during OS migrations (e.g., Win 10 → Win 11) to validate the new OS performs equally or better. |
| **Visualization Type** | Bar Chart |
| **Configuration** | |
| X-axis | `os_name.keyword` |
| Y-axis | `Average` of `activity_response_avg` |
| Break down by | `os_version.keyword` (Top 5) |

---

### Panel 5.3 — Device Volume Distribution

| Setting | Value |
|---|---|
| **Title** | Activity Volume by OS Version |
| **Description** | Shows how activity volume is distributed across OS versions. Helps track OS migration progress and identify stragglers on old versions. |
| **Visualization Type** | Donut Chart |
| **Configuration** | |
| Slice by | `os_version.keyword` |
| Size by | `Sum` of `volume` |

---

## Dashboard 6: SLA & Performance Monitoring

> **Purpose:** Track performance against SLA thresholds. Set up Kibana alerts to notify when SLAs are breached.

### Panel 6.1 — SLA Breach Timeline

| Setting | Value |
|---|---|
| **Title** | SLA Breach Timeline |
| **Description** | Line chart with a horizontal SLA threshold line (e.g., 5000ms). Any point above the line represents an SLA breach. Use for change validation and incident correlation. |
| **Visualization Type** | Line Chart |
| **Configuration** | |
| X-axis | `@timestamp` (Date Histogram) |
| Y-axis | `Average` of `activity_response_avg` |
| Reference line | Horizontal at 5000 (red, dashed, label: "SLA Threshold") |

---

### Panel 6.2 — SLA Breaches by Application

| Setting | Value |
|---|---|
| **Title** | SLA Breaches by Application |
| **Description** | Count of hourly windows where an application's average response time exceeded the SLA threshold. Filter the data view where `activity_response_avg > 5000`. |
| **Visualization Type** | Bar Chart |
| **Configuration** | |
| Filter | `activity_response_avg > 5000` (use Lens formula or saved search filter) |
| X-axis | `application_name.keyword` (Top 10) |
| Y-axis | `Count` (of records above threshold) |

---

### Panel 6.3 — Peak Hours Heat Map

| Setting | Value |
|---|---|
| **Title** | Activity Volume by Hour of Day |
| **Description** | Heat map showing when users are most active. Peak hours should receive priority monitoring and have tighter SLA tracking. Also useful for scheduling maintenance windows. |
| **Visualization Type** | Heat Map |
| **Configuration** | |
| X-axis | Hour of day (use Lens `hour_of_day(@timestamp)` or runtime field) |
| Y-axis | Day of week |
| Cell value | `Sum` of `volume` |
| Color | Blue gradient (light=low, dark=high) |

---

## Dashboard 7: Trend Analysis

> **Purpose:** Long-term trend identification for capacity planning and IT investment decisions.

### Panel 7.1 — Weekly Response Time Trend

| Setting | Value |
|---|---|
| **Title** | Weekly Avg Response Time Trend |
| **Description** | Rolling weekly average response time. Smooths out daily noise to show true performance trajectory. An upward trend demands attention. |
| **Visualization Type** | Line Chart |
| **Configuration** | |
| X-axis | `@timestamp` (Date Histogram, interval: 1 day) |
| Y-axis | `Average` of `activity_response_avg` |
| Moving average | 7-period (use TSVB or Lens formula: `moving_average(average(activity_response_avg), window=7)`) |

---

### Panel 7.2 — Usage Growth Trend

| Setting | Value |
|---|---|
| **Title** | Usage Growth Over Time |
| **Description** | Daily total activity volume trend. An increasing trend means more users or more app usage — plan capacity accordingly. |
| **Visualization Type** | Area Chart |
| **Configuration** | |
| X-axis | `@timestamp` (Date Histogram, interval: 1 day) |
| Y-axis | `Sum` of `volume` |

---

### Panel 7.3 — Wait Time vs Hang Time Trend

| Setting | Value |
|---|---|
| **Title** | Wait Time & Hang Time Trend |
| **Description** | Dual-line chart tracking wait time and hang time over time. Rising hang time indicates apps are freezing more frequently — a serious UX issue. |
| **Visualization Type** | Line Chart |
| **Configuration** | |
| X-axis | `@timestamp` (Date Histogram) |
| Line 1 | `Average` of `wait_time` → label: "Wait Time", color: orange |
| Line 2 | `Average` of `hang_time` → label: "Hang Time", color: red |

---

## Dashboard 8: Activity-Level Drill Down

> **Purpose:** Deep dive into specific activities for troubleshooting.

### Panel 8.1 — All Activities Table

| Setting | Value |
|---|---|
| **Title** | Activity Performance Detail |
| **Description** | Complete table of all activity+application combinations with full metrics. This is the go-to panel for troubleshooting specific user complaints about specific actions. |
| **Visualization Type** | Data Table |
| **Configuration** | |
| Row 1 | `application_name.keyword` (Top 25) |
| Row 2 | `activity_name.keyword` (Top 25) |
| Metrics | `Avg(activity_response_avg)`, `Avg(activity_client_time_avg)`, `Avg(activity_network_time_avg)`, `Avg(activity_backend_time_avg)`, `Sum(volume)` |
| Column labels | "Application", "Activity", "Avg Response", "Client", "Network", "Backend", "Volume" |

---

### Panel 8.2 — Slowest Activities

| Setting | Value |
|---|---|
| **Title** | Top 15 Slowest Activities |
| **Description** | The specific activities with the highest average response time. These represent the exact pain points users experience. |
| **Visualization Type** | Horizontal Bar Chart |
| **Configuration** | |
| Y-axis | `activity_name.keyword` (Top 15, ordered by Avg response) |
| X-axis | `Average` of `activity_response_avg` |
| Color | Red gradient |

---

### Panel 8.3 — Activity Detection Status

| Setting | Value |
|---|---|
| **Title** | Detection Status Breakdown |
| **Description** | Proportion of activities by detection status. A high percentage of "Partial" detections may indicate Aternity agent configuration issues or activity signature problems. |
| **Visualization Type** | Donut Chart |
| **Configuration** | |
| Slice by | `detection_status.keyword` |
| Size by | `Count` |

---

## Kibana Alert Recommendations

Set these up via **Stack Management → Rules and Connectors**:

| Alert Name | Condition | Action |
|---|---|---|
| **High Response Time** | `avg(activity_response_avg) > 10000` over 1 hour | Email / Slack notification |
| **Volume Drop (Possible Outage)** | `sum(volume)` drops > 50% vs previous period | Email / PagerDuty |
| **Network Latency Spike** | `avg(activity_network_time_avg) > 3000` for any location | Email / Slack |
| **Hang Time Increase** | `avg(hang_time) > 5000` for any application | Email / Slack |

---

## Dashboard Layout Recommendation

For the **Executive Overview** dashboard, arrange panels in this grid:

```
┌──────────────────┬──────────────────┬──────────────────┐
│  Total Activities │  Avg Response    │  Unique Users &  │
│  (Metric)        │  Time (Metric)   │  Devices (Metric)│
├──────────────────┴──────────────────┴──────────────────┤
│              Activity Volume Over Time (Area)          │
├────────────────────────────────────────────────────────┤
│              Response Time Trend (Line)                │
├─────────────────────────┬──────────────────────────────┤
│  Top 10 Most Used Apps  │  Top 10 Slowest Apps         │
│  (Horizontal Bar)       │  (Horizontal Bar)            │
├─────────────────────────┴──────────────────────────────┤
│        Activity Distribution by App (Donut)            │
└────────────────────────────────────────────────────────┘
```
