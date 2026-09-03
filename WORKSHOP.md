# 🧭 The Solo Explorer's Self-Guided Workshop

Three short exercises you can do after the session — on this sample data, or better, on your own. No setup beyond `python run.py`.

---

## 1. The Noise Audit  ·  *~15 min*

Goal: feel how much of an alert flood is really a few faults echoing.

1. Run the compass on the sample flood:
   ```bash
   python run.py
   ```
2. Open `data/alerts_noisy.json`. Before reading the output, **guess**: how many *distinct* problems are in these 40 alerts?
3. Compare your guess to the compass headings. What was the dominant `errorCode + API`? How many pages did it suppress?
4. Now the real exercise: export **one hour of your own alerts** to the same JSON shape (`errorCode`, `api`, `service`, `host`, `message`, `ts`). Run the compass on them.
   ```bash
   python run.py --alerts data/your_alerts.json
   ```
   What's *your* loudest signature? That's your highest-leverage thing to fix.

## 2. Extend the Compass  ·  *~30 min*

Goal: make the two agents a little smarter — pick one.

- **New signal:** in `compass/detect_agent.py`, add `severity` or `host`-spread into the ranking so a small-but-critical cluster can out-rank a large-but-warning one.
- **New evidence:** in `compass/investigation_agent.py`, add a rule — e.g. if a config change (not just a deploy) lands in the window, cite it. Extend `context.json` with a `config_changes` list and use it.
- **New echo rule:** teach the investigation agent to recognize a second kind of echo (e.g. a shared dependency causing two services to fail at once).

Re-run to see what changed:
```bash
python run.py
```

## 3. The Mindset Checklist  ·  *keep this one*

For your next solo incident — the human half of the compass. Survival mode vs. explorer mode:

- [ ] **Breathe first.** Name it out loud: "I'm going into the unknown. That's fine — it's territory to map."
- [ ] **Find the heading before the fix.** What's the dominant `errorCode + API`? Don't chase the loudest alert; chase the biggest cluster.
- [ ] **Ask 'what changed?'** Recent deploy to the failing service *or a dependency*? That's usually your first suspect.
- [ ] **Separate echoes from causes.** Is that second alarm a real second problem, or a downstream shadow of the first?
- [ ] **Page narrow.** One clear heading to the right owner beats waking five teams.
- [ ] **Leave a trail.** A one-line note now becomes tomorrow's runbook — and moves the team one step toward wellness.

---

*The unknown is just territory waiting to be explored. Happy navigating. 🧭*
