"""Only provision hardcoded synthetic exercise slots. Never enroll people."""
from auth import ACTORS

def bootstrap(controller):
    for task,actor in [('SYN-R0','SYN-EXPERT-A'),('SYN-R1','SYN-EXPERT-B'),('SYN-R2','SYN-EXPERT-C')]:
        with controller.conn() as db:
            row=db.execute('SELECT actor FROM bindings WHERE task=?',(task,)).fetchone()
        if row:
            if row['actor']!=actor:raise RuntimeError('SYNTHETIC_BINDING_MISMATCH')
            continue
        screen=dict(actor_id=actor,professional_role='SYNTHETIC TEST ROLE',
            nutrition_or_clinical_nutrition_expertise='SYNTHETIC ONLY',years_relevant_practice_or_research=0,
            relevant_decision_experience='ENGINEERING FIXTURE',source_appraisal_experience='ENGINEERING FIXTURE',
            declared_conflicts=[])
        for k in ['prior_exposure_to_exact_case','prior_exposure_to_other_arm_output_for_case',
            'prior_access_to_hidden_diet_values','prior_access_to_SRS_claim_labels',
            'prior_access_to_final_reference','prior_access_to_other_expert_judgment']:screen[k]=False
        controller.qualify(task,actor,screen)
