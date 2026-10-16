import json
from pathlib import Path
from app.config import settings
from app.engine.scanner import ScanFinding

class ComplianceMapper:
    """Loads framework standards, crosswalk mappings, and evaluates control implementation status."""

    def __init__(self, rules_dir: Path | None = None):
        self.rules_dir = rules_dir or settings.compliance_rules_dir
        self.frameworks: dict[str, dict] = {}
        self.crosswalk: list[dict] = []
        self._load_rules()

    def _load_rules(self):
        # 1. Load framework registry
        frameworks_file = self.rules_dir / "frameworks.json"
        if frameworks_file.exists():
            try:
                data = json.loads(frameworks_file.read_text(encoding="utf-8"))
                for fw in data.get("frameworks", []):
                    # Load full controls file
                    ctrl_file = self.rules_dir / fw["file"]
                    if ctrl_file.exists():
                        fw_detail = json.loads(ctrl_file.read_text(encoding="utf-8"))
                        self.frameworks[fw["id"]] = fw_detail
            except Exception as e:
                print(f"Error loading framework rules: {e}")

        # 2. Load crosswalk mappings
        cw_file = self.rules_dir / "crosswalk_mappings.json"
        if cw_file.exists():
            try:
                data = json.loads(cw_file.read_text(encoding="utf-8"))
                self.crosswalk = data.get("mappings", [])
            except Exception as e:
                print(f"Error loading crosswalk mappings: {e}")

    def get_all_frameworks(self) -> list[dict]:
        """Returns all loaded frameworks with their controls."""
        results = []
        for fid, fw in self.frameworks.items():
            results.append({
                "id": fid,
                "name": fw.get("name", fid),
                "version": fw.get("version", "1.0"),
                "publisher": fw.get("publisher", "Independent Academic Reference"),
                "category": fw.get("category", "Security & AI Governance"),
                "controls_count": len(fw.get("controls", [])),
                "source_url": fw.get("source_url", ""),
                "disclaimer": fw.get("disclaimer", ""),
                "controls": fw.get("controls", [])
            })
        return results

    def evaluate_controls(
        self,
        findings: list[ScanFinding],
        target_frameworks: list[str],
        recon_summary: dict | None = None
    ) -> list[dict]:
        """
        Maps scanner findings and architecture evidence to framework controls.
        Determines control status:
        - IMPLEMENTED_WITH_EVIDENCE
        - PARTIALLY_IMPLEMENTED
        - MISSING_WITH_EVIDENCE
        - NOT_EVIDENCED
        - NOT_APPLICABLE
        """
        results = []
        recon = recon_summary or {}
        components = recon.get("components", [])
        has_vector_store = any("vector" in str(c).lower() for c in components)
        has_os_tools = any("shell" in str(c).lower() or "subprocess" in str(c).lower() for c in components)

        # Index findings by category and owasp_id
        findings_by_category: dict[str, list[ScanFinding]] = {}
        for f in findings:
            findings_by_category.setdefault(f.category, []).append(f)

        # Build reverse crosswalk lookup: target_framework -> target_control_id -> list of mappings
        control_mapping_lookup: dict[str, dict[str, list[dict]]] = {}
        for map_entry in self.crosswalk:
            src_cat = map_entry.get("source_category")
            owasp_id = map_entry.get("owasp_id")
            for tc in map_entry.get("target_controls", []):
                tf_id = tc["framework_id"]
                tc_id = tc["control_id"]
                control_mapping_lookup.setdefault(tf_id, {}).setdefault(tc_id, []).append({
                    "source_category": src_cat,
                    "owasp_id": owasp_id,
                    "mapping_type": tc.get("mapping_type", "CONCEPTUAL"),
                    "rationale": tc.get("rationale", "")
                })

        for fw_id in target_frameworks:
            fw_data = self.frameworks.get(fw_id)
            if not fw_data:
                continue

            for ctrl in fw_data.get("controls", []):
                ctrl_id = ctrl["control_id"]
                title = ctrl["title"]
                cat = ctrl.get("category", "")
                source_url = ctrl.get("reference_url", fw_data.get("source_url", ""))
                is_conceptual = ctrl.get("is_conceptual_mapping", False)

                # Check if this control applies to this application architecture
                # E.g. Vector embedding weaknesses only applicable if RAG / Vector store exists
                if ctrl_id in ("LLM08", "AML.T0043") and not has_vector_store and len(findings_by_category.get("VECTOR_EMBEDDING_WEAKNESS", [])) == 0:
                    status = "NOT_APPLICABLE"
                    evidence_summary = "Application architecture does not utilize retrieval-augmented vector databases."
                    rationale = "Control is scoped specifically to RAG/vector store pipelines."
                    is_conc = False
                elif fw_id == "OWASP-GENAI":
                    # Direct check against findings matching this OWASP control ID
                    matching_findings = [f for f in findings if f.owasp_id == ctrl_id]
                    if any(f.severity in ("CRITICAL", "HIGH") for f in matching_findings):
                        status = "MISSING_WITH_EVIDENCE"
                        evidence_summary = f"{len(matching_findings)} vulnerability finding(s) detected directly compromising this control."
                        rationale = f"Detected confirmed violations in code: {', '.join(f.finding_id for f in matching_findings[:3])}."
                        is_conc = False
                    elif len(matching_findings) > 0:
                        status = "PARTIALLY_IMPLEMENTED"
                        evidence_summary = f"{len(matching_findings)} medium/low findings or warnings identified."
                        rationale = f"Partial mitigation detected with residual gaps: {', '.join(f.finding_id for f in matching_findings[:3])}."
                        is_conc = False
                    else:
                        # No vulnerabilities found for this category
                        # If documented as implemented or other controls present
                        status = "NOT_EVIDENCED"
                        evidence_summary = "No vulnerability detected in static analysis, but no formal verification test was discovered in inspected files."
                        rationale = "Absence of detected vulnerability does not prove complete control verification."
                        is_conc = False
                else:
                    # Mapped via crosswalk
                    mappings = control_mapping_lookup.get(fw_id, {}).get(ctrl_id, [])
                    if mappings:
                        relevant_findings = []
                        rationales = []
                        for m in mappings:
                            src_cat = m["source_category"]
                            if src_cat in findings_by_category:
                                relevant_findings.extend(findings_by_category[src_cat])
                                rationales.append(m["rationale"])
                            if m["mapping_type"] == "CONCEPTUAL":
                                is_conceptual = True

                        if any(f.severity in ("CRITICAL", "HIGH") for f in relevant_findings):
                            status = "MISSING_WITH_EVIDENCE"
                            evidence_summary = f"Identified {len(relevant_findings)} critical/high finding(s) breaking control objectives."
                            rationale = " | ".join(rationales[:2]) or "Vulnerability evidence contradicts control implementation."
                        elif len(relevant_findings) > 0:
                            status = "PARTIALLY_IMPLEMENTED"
                            evidence_summary = f"Identified {len(relevant_findings)} medium/low finding(s) requiring remediation."
                            rationale = " | ".join(rationales[:2]) or "Partial control coverage observed."
                        else:
                            status = "NOT_EVIDENCED"
                            evidence_summary = "No vulnerability directly violated this control in evaluated source artifacts."
                            rationale = "Requires runtime operational audit and formal security policy evidence."
                    else:
                        status = "NOT_EVIDENCED"
                        evidence_summary = "No direct static code signature available for this governance control."
                        rationale = "General organizational/policy control; not evidenced in inspected technical code."

                results.append({
                    "framework_id": fw_id,
                    "control_id": ctrl_id,
                    "control_title": title,
                    "control_category": cat,
                    "status": status,
                    "evidence_summary": evidence_summary,
                    "rationale": rationale,
                    "source_url": source_url,
                    "is_conceptual": is_conceptual
                })

        return results
