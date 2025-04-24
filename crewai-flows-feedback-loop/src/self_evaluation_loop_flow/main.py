#!/usr/bin/env python
import json
import pymupdf4llm
from typing import Optional
from pydantic import BaseModel

from crewai.flow.flow import Flow, listen, start, router, or_
from .crews.jsoncrafter_crew.jsoncrafter_crew import JsoncrafterCrew
from .crews.jsonvalidator_crew.jsonvalidator_crew import JsonvalidatorCrew
from .crews.droolscrafter_crew.droolscrafter_crew import DroolscrafterCrew  
from .crews.droolsvalidator_crew.droolsvalidator_crew import DroolsvalidatorCrew  

# Read SOP Document
sop_text = pymupdf4llm.to_markdown("C:/Users/gunravi/Desktop/personal_projects/crewai-flows/self_evaluation_loop_flow/src/self_evaluation_loop_flow/POC_Auth_GBD_12_09_2024.pdf")

# Define the state of the flow
class SOPRuleFlowState(BaseModel):
    json_sop: str = ""
    json_feedback: Optional[str] = None
    json_valid: bool = False
    json_accuracy_score: float = 0
    json_retry_count: int = 0
    
    drools_sop: str = ""
    drools_feedback: Optional[str] = None
    drools_valid: bool = False
    drools_accuracy_score: float = 0
    drools_retry_count: int = 0


class SOPRuleFlow(Flow[SOPRuleFlowState]):

    @start("json_retry")
    def generate_json_sop(self):
        result = JsoncrafterCrew().crew().kickoff(
            inputs={"sop_text": sop_text,"feedback":self.state.json_feedback}
        )
        print("result :",result)
        self.state.json_sop = result['json_sop']

    @router(generate_json_sop)
    def evaluate_json_sop(self):

        if self.state.json_retry_count > 3:
            return "json_max_retry_exceeded"

        result = JsonvalidatorCrew().crew().kickoff(inputs={"sop_text": sop_text,"sop_json":self.state.json_sop})
        self.state.json_valid = result["valid"]
        self.state.json_accuracy_score = result["accuracy_score"]
        self.state.json_feedback = result["feedback"]

        print("json valid: ", self.state.json_valid)
        print("jso accuracy_score: ", self.state.json_accuracy_score)
        print("jso feedback: ", self.state.json_feedback)
        self.state.json_retry_count += 1

        if self.state.json_valid and self.state.json_accuracy_score > 80:
            return "generate_drools"

        print("JSON RETRY")
        return "json_retry"

    # @listen("completed")
    # def save_results(self):
    #     print("json sop is valid with above 80% accuracy")
    #     print("json sop:", self.state.json_sop)

    #     # Save the valid X post to a file
    #     with open("json_sop.json", 'w') as json_file:
    #         json.dump(self.state.json_sop, json_file, indent=4)  # `indent=4` makes it pretty-printed for readability

    # @listen("json_max_retry_exceeded")
    # def json_max_retry_exceeded(self):
    #     print("Json Max retry count exceeded")
    #     print("json sop:", self.state.json_sop)
    #     print("Feedback:", self.state.json_feedback)

    @listen("generate_drools")
    def generate_drools_sop(self):
        result = DroolscrafterCrew().crew().kickoff(
            inputs={"json_sop": self.state.json_sop, "feedback": self.state.drools_feedback}
        )
        self.state.drools_sop = result['drools_sop']
        print("Drools SOP:", self.state.drools_sop)

    @router(generate_drools_sop)
    def evaluate_drools_sop(self):
        if self.state.drools_retry_count > 3:
            return "drools_max_retry_exceeded"

        result = DroolsvalidatorCrew().crew().kickoff(
            inputs={"json_sop": self.state.json_sop, "drools_sop": self.state.drools_sop}
        )
        self.state.drools_valid = result["valid"]
        self.state.drools_accuracy_score = result["accuracy_score"]
        self.state.drools_feedback = result["feedback"]

        print("Drools valid:", self.state.drools_valid)
        print("Drools accuracy_score:", self.state.drools_accuracy_score)
        print("Drools feedback:", self.state.drools_feedback)
        self.state.drools_retry_count += 1

        if self.state.drools_valid and self.state.drools_accuracy_score > 80:
            return "completed"

        print("DROOLS RETRY")
        return "generate_drools"

    @listen("completed")
    def save_results(self):
        print("Both JSON and Drools SOPs are valid with above 80% accuracy")
        print("JSON SOP:", self.state.json_sop)
        print("Drools SOP:", self.state.drools_sop)

    @listen("json_max_retry_exceeded")
    def json_max_retry_exceeded_exit(self):
        print("Max retry count exceeded for JSON SOP")
        print("JSON SOP:", self.state.json_sop)
        print("JSON Feedback:", self.state.json_feedback)

    @listen("drools_max_retry_exceeded")
    def drools_max_retry_exceeded_exit(self):
        print("Max retry count exceeded for Drools SOP")
        print("Drools SOP:", self.state.drools_sop)
        print("Drools Feedback:", self.state.drools_feedback)

    

def kickoff():
    SOPRule_flow = SOPRuleFlow()
    SOPRule_flow.kickoff()


def plot():
    SOPRule_flow = SOPRuleFlow()
    SOPRule_flow.plot()


if __name__ == "__main__":
    kickoff()
