# agent.py

import yaml
import os
import difflib
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from click_handler import click_next_button  # :contentReference[oaicite:0]{index=0}&#8203;:contentReference[oaicite:1]{index=1}

class QAAgent:
    def __init__(self, driver, resume_path="resume_data.yaml", override_path="qa_mapping.yaml"):
        self.driver = driver
        # 1) load your resume data
        with open(resume_path) as f:
            self.resume = yaml.safe_load(f)
        # 2) load any manual overrides
        with open(override_path) as f:
            self.overrides = yaml.safe_load(f) or {}
        self.override_path = override_path
        # 3) flatten resume into list of (path, value) pairs
        self.flat = []
        self._flatten(self.resume)

    def _flatten(self, curr, path=None):
        path = path or []
        if isinstance(curr, dict):
            for k, v in curr.items():
                self._flatten(v, path + [k])
        elif isinstance(curr, list):
            for i, v in enumerate(curr):
                self._flatten(v, path + [f"[{i}]"])
        else:
            self.flat.append((".".join(path), str(curr)))

    def _match_override(self, question):
        # exact or fuzzy in overrides
        if question in self.overrides:
            return self.overrides[question]
        # fuzzy match on question keys
        keys = list(self.overrides.keys())
        close = difflib.get_close_matches(question, keys, n=1, cutoff=0.7)
        return self.overrides[close[0]] if close else None

    def _match_resume(self, question):
        # find the best (path, value) by fuzzy‑matching question vs path+value
        best_score, best_pair = 0, None
        for path, val in self.flat:
            candidate = (path + " " + val).lower()
            score = difflib.SequenceMatcher(None, question.lower(), candidate).ratio()
            if score > best_score:
                best_score, best_pair = score, (path, val)
        return best_pair if best_score > 0.6 else None

    def answer_next(self):
        # 1) grab the question text
        q = self.driver.find_element(By.CSS_SELECTOR, ".question-text").text.strip()

        # 2) check manual override
        entry = self._match_override(q)
        if entry:
            typ, ans = entry["type"], entry["answer"]
        else:
            # 3) try to pull from resume_data.yaml
            match = self._match_resume(q)
            if match:
                _, ans = match
                typ = "text"       # or infer dropdown/mcq if you like
            else:
                # 4) fallback: ask the user, then save override
                opts = [o.text for o in self.driver.find_elements(
                          By.XPATH, ".//following-sibling::*//option")]
                print(f"\n❓ {q}\nOptions: {opts}")
                idx = int(input("Choose index: "))
                ans = opts[idx]
                typ = "dropdown"
                self.overrides[q] = {"type": typ, "answer": ans}
                with open(self.override_path, "w") as f:
                    yaml.safe_dump(self.overrides, f)

        # 5) fill the form
        if typ == "dropdown":
            sel = Select(self.driver.find_element(By.TAG_NAME, "select"))
            sel.select_by_visible_text(ans)
        elif typ == "mcq":
            self.driver.find_element(By.XPATH,
                f"//label[contains(., '{ans}')]").click()
        elif typ == "text":
            inp = self.driver.find_element(By.TAG_NAME, "input")
            inp.clear(); inp.send_keys(ans)
        else:
            raise NotImplementedError(f"No handler for {typ}")

        # 6) click next
        click_next_button(self.driver)
