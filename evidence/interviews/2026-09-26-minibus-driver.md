# User Interview Notes: Green Minibus Driver (Aberdeen Corridor)

- **Date:** 2026-09-26
- **Participant Profile:** Anonymous Experienced Green Minibus Driver (~15 years experience, Aberdeen/Pok Fu Lam routes)
- **Interviewer:** Component H Lead
- **Methodology:** 15-minute standard 6-question structured interview followed by a 5-minute system concept user response test.

These are the interviewer's notes from one participant, not a verbatim transcript or a representative survey. The trust levels below are qualitative; no percentages were measured. Check any proposed direct quote against the recording or original notes before using it publicly.

---

## Part 1: Core Questions (Current Behavior & Pain Points)

### Q1: When a road you use closes, how do you find out?
- **Primary Source:** Peer WhatsApp groups (drivers sharing realtime photos, video clips, and text notices). Far faster than official Transport Department (TD) notices, which usually arrive after heavy congestion has already formed.
- **Secondary Source:** On-site visual observation (road closures, police presence, work zones around Pok Fu Lam Rd, Aberdeen Tunnel, or Cyberport).
- **Other Sources:** Passengers occasionally mention closures; official apps/radio broadcasts are checked only as backup.

### Q2: What do you do in the first ten minutes?
1. **Check WhatsApp Groups:** Read driver reports on which roads are closed, expected duration, and peer recommendations.
2. **Assess Current Location & Reroute:** If not yet in the queue, immediately turn/u-turn to backup routes (e.g., bypass via Wah Fu, Cyberport, or alternate tunnel exits).
3. **Notify Passengers:** Inform passengers briefly ("Road ahead is closed, rerouting will take slightly longer") to manage expectations.

### Q3: Who tells you anything, and how much do you trust it?
- **High Trust:** Peer driver WhatsApp groups and live photo/video evidence from colleagues on the same corridor.
- **Direct Observation Trusted Most:** Police officers, barriers, and queue length seen firsthand.
- **Lower Trust:** Passenger comments, which the participant described as sometimes inaccurate or hearsay.
- **Lowest Trust:** TD App / Commercial Radio / Official news (notoriously delayed, used only for secondary verification).

### Q4: When official advice says "use an alternative route", do you take it?
- **Usually NO.** Official recommendations suggest major trunk roads that are often already jammed or unsuitable for green minibuses (e.g., Pok Fu Lam Road or Nam Fung Road have bottlenecks, narrow sections, or steep inclines).
- **Preference:** Follow peer recommendations or use unannounced residential/back-alley shortcuts based on local domain knowledge.

### Q5: What would you want to know that nobody tells you today?
1. **Accurate Incident Duration:** Honest estimates of actual clearance time rather than vague "estimated 2 hours" or "until further notice".
2. **Real-time Secondary Corridor Status:** Live traffic conditions on candidate alternative routes (whether they are already jammed or if police are setting up secondary barriers).

### Q6: Who else is deciding at the same moment as you?
- Peer minibus drivers, taxi drivers, and experienced private vehicle drivers on the road. Passengers rely on the driver; bus drivers have fixed routes; police/TD make management decisions independently of real-time driving tactical decisions.

---

## Part 2: Product Brief & System Response Test

**Prompt Presented to Participant:**

The incident, delay, diversion, and savings figures in this concept prompt were hypothetical interview stimuli. They are not measured Ripple results and must not be reused as evidence of performance.

- Incident: 3:00 PM Aberdeen Tunnel exit accident, 45-min delay.
- System Advisory: "Aberdeen Tunnel exit accident, queue back to Wong Chuk Hang. Recommend Pok Fu Lam Rd or Nam Fung Rd, saving ~12 mins."
- System Impact Metric: "30% vehicle diversion avoids 740 hours of cumulative delay."

### Key Reactions & Observations:

#### 1. What they LIKED / Valued:
- Appreciated bilingual, clear Cantonese notification phrasing.
- Valued specific local landmark references (e.g., "queue back to Wong Chuk Hang").

#### 2. What they IGNORED / Questioned:
- **Ignored Aggregate System Data:** Completely disregarded the "740 hours of cumulative delay saved" macro metric. Stated macro impact numbers are useless for real-time tactical driving.
- **Skeptical of Delay Savings Estimate:** Expressed deep skepticism about "saves 12 mins via Pok Fu Lam Rd", noting Pok Fu Lam Rd is routinely congested in the afternoon and Nam Fung Rd has narrow geometric limits for minibuses.
- **Verification First:** Stated they would *never* reroute immediately upon seeing the app advisory; they would first cross-check in their driver WhatsApp group to verify whether Pok Fu Lam Rd is *actually* moving before turning.

---

## Key Takeaways for Component H (Pitch & System Design)

1. **Internal paraphrase for the pitch / Q&A (not a verified direct quote):** The participant said they would check with other drivers that a suggested route was moving before trusting a time-savings claim. Verify against the source interview before quoting them directly.
2. **HMI & Design Implications to discuss:**
   - This participant valued local route conditions more than an aggregate person-hours metric. Consider showing the status and uncertainty of suggested routes; test whether other drivers share this preference.
   - Check whether candidate routes are suitable for green minibuses before recommending them. Any new vehicle-class constraint or contract change needs a separate decision by the relevant owners.
