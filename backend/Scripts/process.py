from llama_index.llms.gemini import Gemini
from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core import Settings
from llama_index.core.tools import QueryEngineTool
from llama_index.core.query_engine.router_query_engine import RouterQueryEngine
from llama_index.core.selectors import LLMSingleSelector
import google.generativeai as genai
import re
from dotenv import load_dotenv
import json
import os
import nest_asyncio
import pymupdf4llm
from llama_index.core import SummaryIndex, VectorStoreIndex
from langchain_google_vertexai import VertexAIEmbeddings
import time
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)
llm=Gemini()
# PROJECT_ID = 'white-watch-436805-d1'
# REGION = 'us-central1'
# MODEL_ID = 'text-embedding-004'
class DocumentProcessor:
    def __init__(self, pdf_url):
        self.pdf_url = pdf_url
        self.document = ""
        self.nodes = None
        self.full_text=None
    def process_to_text(self):
        md_text = pymupdf4llm.to_markdown(self.pdf_url,pages=[1,2,3,4,5,6,7,8,9,10,11])
        self.full_text=md_text
        # self.document = Document(text=md_text)
        # splitter = SentenceSplitter(chunk_size=1024)
        # self.nodes = splitter.get_nodes_from_documents([self.document])
    def process_to_nodes(self):
        self.document = Document(text=self.full_text)
        splitter = SentenceSplitter(chunk_size=2000,chunk_overlap=200)
        self.nodes = splitter.get_nodes_from_documents([self.document])        

class EmbeddingModel:
    @staticmethod
    def get_embedding_model():
        # lc_embed_model = HuggingFaceEmbeddings(
        #     model_name="sentence-transformers/all-mpnet-base-v2"
        # )
        embeddings = VertexAIEmbeddings(model_name="text-embedding-005")

        return embeddings#LangchainEmbedding(lc_embed_model)

class IndexBuilder:
    def __init__(self, nodes):
        self.nodes = nodes
        #self.summary_index = None
        self.vector_index = None

    def build_indices(self):
        #self.summary_index = SummaryIndex(self.nodes)
        self.vector_index = VectorStoreIndex(self.nodes)

class QueryEngineBuilder:
    def __init__(self, vector_index):
        #self.summary_index = summary_index
        self.vector_index = vector_index
        self.query_engine = None

    def build_query_engine(self):
        # summary_query_engine = self.summary_index.as_query_engine(
        #     response_mode="tree_summarize",
        #     use_async=True,
        # )
        vector_query_engine = self.vector_index.as_query_engine(vector_store_query_mode="mmr",vector_store_kwargs={"mmr_threshold":0.2})

        # summary_tool = QueryEngineTool.from_defaults(
        #     query_engine=summary_query_engine,
        #     description="Useful for summarization questions related to the cybersecurity audit report"
        # )

        vector_tool = QueryEngineTool.from_defaults(
            query_engine=vector_query_engine,
             description="Useful for question answering from the cybersecurity audit report"
        )

        self.query_engine = RouterQueryEngine(
            selector=LLMSingleSelector.from_defaults(),
            query_engine_tools=[vector_tool],
            verbose=True
        )

class CybersecurityFindingsExtractor:
    def __init__(self):
         self.llm = Gemini()
         Docobj=DocumentProcessor()
         Docobj.process_to_text()
         self.ref_text=Docobj.full_text
     
    def extract_findings(self):
        prompt = """
        Analyze a cybersecurity report and provide the key findings in a structured format. 
        The output should be in JSON format with a well-structured hierarchy. 
        Each main category should have subcategories and descriptions.

        Report content:\n
        """+self.ref_text+"""


        Analyze the following cybersecurity report and provide key findings in JSON format. The response must adhere to a clear hierarchical structure, focusing on the following categories:

        Threat Landscape: Overview of emerging threats and attack vectors, along with their impact.
        Vulnerabilities: List of top vulnerabilities identified (without severity ratings).
        Incident Response: Summary of recent incidents and evaluation of response strategies.
        Emerging Technologies: How new technologies are affecting cybersecurity and associated risks.
        Compliance and Regulatory Issues: Current compliance challenges and recent regulatory updates.
        Ensure that the JSON response is well-structured, and each category is described clearly and concisely. The findings should be actionable and relevant for cybersecurity professionals.

        
        Format the output as a JSON list of objects, each ALWAYS containing ONE EACH of:
        {
        "Threat Landscape": {
            "Emerging Threats": {
                "description": "Overview of new and evolving cyber threats",
                "examples": ["Threat 1", "Threat 2"],
                "impact": "Potential impact on systems and data"
            },
            "Attack Vectors": {
                "common_methods": ["Method 1", "Method 2"],
                "trends": "Recent trends in how attacks are executed"
            }
            },
        "Vulnerabilities": {
            "Critical Issues": {
                "top_vulnerabilities": ["Vulnerability 1", "Vulnerability 2"]
                }
            },
        "Incident Response": {
            "Recent Incidents": {
                "description": "Analysis of recent incidents and attack patterns",
                "response_effectiveness": "Evaluation of response strategies"
                }
            },
        "Emerging Technologies": {
            "Impact": {
                "description": "How new technologies are affecting cybersecurity",
                "associated_risks": ["Risk 1", "Risk 2"]
                }
            },
        "Compliance and Regulatory Issues": {
            "Challenges": {
                "description": "Current compliance challenges faced",
                "regulatory_updates": "Recent regulatory updates"
                }
            }
        }
        Provide a comprehensive analysis that a cybersecurity professional would find informative and actionable.
        """

        response = self.process_prompt(prompt)
        json_match = re.search(r"\[([\s\S]*?)\]$", response)
        if json_match:
            json_str = json_match.group(1)
            #print(json_str)       
        else:
            json_str = response
        return self.extract_and_validate_json(json_str)

    def process_prompt(self, prompt):
        try:
            response = self.llm.complete(prompt)
            return response
        except Exception as e:
            return f"An error occurred while processing the prompt: {e}"

    def extract_and_validate_json(self, text):
        pattern = r"\[.*\]"
        matches = re.findall(pattern, text, re.DOTALL)
        
        if matches:
            json_text = matches[-1]  
            try:
                json_data = json.loads(json_text)
                # if self.validate_json_structure(json_data):
                return json_data
                # else:
                #     return "JSON structure is not sufficiently detailed or well-structured."
            except json.JSONDecodeError:
                return f" JSON not proper in the output.{text}"
        else:
            return f"No JSON found in the output.{text}"

    # def validate_json_structure(self, json_data):
    #     if not isinstance(json_data, dict) or len(json_data) < 3:
    #         return False
    #     for value in json_data.values():
    #         if not isinstance(value, dict) or len(value) < 1:
    #             return False
    #         for subvalue in value.values():
    #             if not isinstance(subvalue, (dict, list, str)):
    #                 return False
    #     return True

##################################
##################################

class VulnerabilityExtractorAndRanker:
    def __init__(self, cybersecurity_findings):
        self.llm = Gemini()
        self.cybersecurity_findings = cybersecurity_findings

    def extract_and_rank_vulnerabilities(self):
        prompt = f"""
        Analyze the following cybersecurity findings and extract a list of vulnerabilities. 
        Then, rank these vulnerabilities from most critical to least critical.

        Cybersecurity Findings:
        {json.dumps(self.cybersecurity_findings, indent=2)}

        For each vulnerability:
        1. Provide a brief description
        2. Assign a criticality score from 1-10 (10 being most critical)
        3. Explain the reasoning behind the criticality score

        Format the output as a JSON list of objects, each ALWAYS containing ONE EACH of:
        - "vulnerability": (string) Name or brief description of the vulnerability
        - "criticality_score": (number) Score from 1-10
        - "reasoning": (string) Explanation for the score
        - "mitigation": (string) Brief suggestion for mitigation

        Sort the list by criticality_score in descending order.

        Example:
        [
          {{
            "vulnerability": "Unpatched software with known exploits",
            "criticality_score": 9,
            "reasoning": "Easily exploitable and can lead to full system compromise",
            "mitigation": "Implement regular patching schedule and vulnerability scanning"
          }},
          ...
        ]
        """

        response = self.llm.complete(prompt)
        return self.parse_vulnerabilities(response.text)

    def parse_vulnerabilities(self, response):
        json_match = re.search(r'\[[\s\S]*\]', response)
        if json_match:
            try:
                vulnerabilities = json.loads(json_match.group())
                return sorted(vulnerabilities, key=lambda x: x['criticality_score'], reverse=True)
            except json.JSONDecodeError:
                return "Error: Unable to parse the vulnerability list as JSON."
        else:
            return "Error: No valid JSON found in the response."

#############################
#############################
class DocumentQuerySystem:
    def __init__(self, pdf_url):
        nest_asyncio.apply()
        Settings.llm = Gemini()
        Settings.embed_model = EmbeddingModel.get_embedding_model()

        self.document_processor = DocumentProcessor(pdf_url)
        self.document_processor.process_to_text()
        self.document_processor.process_to_nodes()
        self.full_text=self.document_processor.full_text
        self.index_builder = IndexBuilder(self.document_processor.nodes)
        self.index_builder.build_indices()

        self.query_engine_builder = QueryEngineBuilder(
            #self.index_builder.summary_index,
            self.index_builder.vector_index
        )
        self.query_engine_builder.build_query_engine()
    def summarize(self):        
        summarization_prompt = f"""
        Please provide a detailed summary of all events, activities, or occurrences mentioned in the following company document that can potentially impact the company's Environmental (E), Social (S), and Governance (G) values. 
        The summary should:
        1. Identify and categorize each event under Environmental, Social, or Governance aspects, clearly stating how it may affect the respective value.
        2. Highlight any significant trends, actions, or incidents related to these ESG categories.
        3. Provide brief explanations of why each event is relevant to ESG considerations.
        4. Be concise yet comprehensive, aiming for about 300 words, and ensure all potential ESG-impacting events are listed and categorized appropriately.

        Document to analyze:

        {self.document_processor.full_text}

        ESG Event Summary:
        """


        response = llm.complete(summarization_prompt)
        return response
     
    def query(self, question):
        return self.query_engine_builder.query_engine.query(question)

def extract_json_with_regex(response_text):
    """
    Extracts the JSON part of the text using a regular expression.

    Args:
        response_text (str): The raw text response from the LLM.

    Returns:
        str: Extracted JSON string or None if not found.
    """
    response_text = str(response_text)  # Ensure response_text is a string
    match = re.search(r'(\{[\s\S]*\})', response_text)
    return match.group(1) if match else None


def parse_llm_response(response_text, max_retries=3, retry_delay=1.0):
    """
    Extracts and parses the JSON content from a GenerateContentResponse object using regex.
    Retries if parsing fails.

    Args:
        llm_response: The GenerateContentResponse object from the LLM.
        max_retries (int): Maximum number of retries if JSON parsing fails.
        retry_delay (float): Delay between retries in seconds.

    Returns:
        dict: Parsed JSON response or an error message if parsing fails.
    """
    for attempt in range(max_retries):
        try:
            # Extract raw response text from the LLM response
            response_text = str(response_text)
            print(response_text)
            json_text = extract_json_with_regex(response_text)
            if not json_text:
                raise ValueError("No JSON content found in the response.")

            return json.loads(json_text)

        except (json.JSONDecodeError, ValueError) as e:
            print(f"Attempt {attempt + 1}: JSON parsing failed with error: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)  # Retry with a delay
            else:
                return {"response": "Failed to parse the LLM response after multiple attempts.", "status": 0}
        
        except KeyError as e:
            return {"response": f"Error accessing required fields: {e}", "status": 0}











def answer_with_llm(scenario: str,string="") -> dict:
    """
    Sends a scenario to an LLM and processes the response.

    Args:
        scenario (str): Input describing a scenario.

    Returns:
        dict: Processed response with keys "response" and "status".
    """
    # Construct the prompt for the LLM
    prompt = f"""
    You are an assistant evaluating businesses based on how their esg data would be. Your goal is to know the businesses's projects and relevant ESG scores alone clearly. 
    Based on the input scenario:
    - If you are certain about the businesses's PERSONA to be able to evaluate their ESG scores, respond with "status: 1" and a thank-you message.
    - If you have any uncertainty, respond with "status: 0" and a follow-up question requesting more clarification.
    - Ask at least 2 doubts
    The input scenario is:
    "{scenario}"

    Here are two examples of how you should respond:

    Example 1 (When the LLM still has uncertainty):
    Scenario: "I am still a bit uncertain about the process."
    Response:
    {{
        "response": "Could you clarify or provide more details about this topic(describe the topic)",
        "status": 0
    }}

    Example 2 (When the LLM is clear and understands everything):
    Scenario: "Everything is clear and I have no doubts."
    Response:
    {{
        "response": "Thank you! I have understood everything.",
        "status": 1
    }}

    Please respond with ONLY the JSON object, nothing else.
    """

    llm_response = llm.complete(prompt)

    # Parse and return the LLM response
    return parse_llm_response(llm_response)

def interact_with_user(summary:str):
    """
    Interactive session with the user.
    """
    scenario = "Summary until now\n"+str(summary)
    string=f'''\nThe user's responses until now:'''
    while True:
        result = answer_with_llm(scenario,string)
        print(f"LLM: {result['response']}") 
        #string=string+"\n"+result['response'] 

        if result["status"] == 1:
            print("Conversation ended.")
            break
        else:
            # Otherwise, prompt the user for further clarification
            scenario = input("Your clarification or follow-up: ")
            string=string+"\n"+scenario

def extract_and_validate_json( text):
    pattern = r"\[.*\]"
    matches = re.findall(pattern, text, re.DOTALL)
        
    if matches:
        json_text = matches[-1]  
        try:
            json_data = json.loads(json_text)
                # if self.validate_json_structure(json_data):
            return json_data
                # else:
                #     return "JSON structure is not sufficiently detailed or well-structured."
        except json.JSONDecodeError:
            return f" JSON not proper in the output.{text}"
    else:
        return f"No JSON found in the output.{text}"



def return_metrics(summary: str):
    summarization_prompt = f"""
    Instruction:
    Using the provided summary of ESG-affecting events, generate a JSON object that categorizes the Environmental (E), Social (S), and Governance (G) indicators based on their relevance to the described events. For each category, include a list of indicators, where each indicator is represented as an object with the following fields:

    - **indicator**: The name of the indicator relevant to the events.
    - **weight**: The weight of the indicator (a number between 0 and 1). The sum of all weights within each category must equal 1.
    - **score**: The raw score of the indicator (a number between 0 and 100), reflecting the company's performance in this area based on the described events.

    Example JSON Format:
    {{
    "E": [
        {{ "indicator": "Carbon Emissions", "weight": 0.4, "score": 85 }},
        {{ "Energy Efficiency", "weight": 0.3, "score": 90 }},
        {{ "Water Usage", "weight": 0.3, "score": 75 }}
    ],
    "S": [
        {{ "indicator": "Labor Practices", "weight": 0.5, "score": 80 }},
        {{ "Diversity & Inclusion", "weight": 0.3, "score": 70 }},
        {{ "Community Engagement", "weight": 0.2, "score": 85 }}
    ],
    "G": [
        {{ "indicator": "Board Independence", "weight": 0.4, "score": 90 }},
        {{ "Executive Compensation", "weight": 0.3, "score": 70 }},
        {{ "Transparency", "weight": 0.3, "score": 80 }}
    ]
    }}

    **Input:**
    Summary of ESG-Affecting Events:
    {summary}

    **Task:**
    Based on the provided summary, create a JSON object with:
    1. Indicators that best align with the events described in the document.
    2. Appropriate weights for each indicator within E, S, and G, ensuring the weights sum to 1 for each category.
    3. Relevant scores for each indicator, reflecting the company's performance as suggested by the described events.

    **Output:**
    Return the JSON object formatted as shown in the example.
    """
    response = llm.complete(summarization_prompt)
    return extract_and_validate_json(extract_json_with_regex(response))



if __name__ == "__main__":
    pdf_url = "/home/shadowx/shaastra25/backend/assets/NASDAQ_AAPL_2023.pdf"
    query_system = DocumentQuerySystem(pdf_url)
    response = query_system.summarize()
    print(return_metrics(response))
    #print(response)
    #interact_with_user(response)
    #print(str(response))
    # Cyber_obj=CybersecurityFindingsExtractor()
    # findings=Cyber_obj.extract_findings()
    # print(json.dumps(findings,indent=2))
    # extractor = VulnerabilityExtractorAndRanker(findings)
    # ranked_vulnerabilities = extractor.extract_and_rank_vulnerabilities()
    
    # print(json.dumps(ranked_vulnerabilities, indent=2))
    # llm=Gemini()
    # Doc=Cyber_obj.ref_text
    # response=llm.complete()
    # print(response)
    #hello=input()
    #print(query_system.query(f"""[SYSTEM MESSAGE]
                                        #  You are now adopting the persona of Fischer, a knowledgeable and friendly AI assistant
                                        #  from the CyberStrike AI Audit Management Suite. Your primary role is to assist users in
                                        #  navigating cybersecurity audit processes, providing insights, and enhancing the overall 
                                        #  quality of audit reports. Emphasize your expertise in risk assessments, compliance, 
                                        #  vulnerability analysis, and remediation recommendations. Be personable, approachable, 
                                        #  and solution-oriented.
                                        #  ONLY SAY "Hi there! I'm Fischer, your friendly AI assistant from CyberStrike." ONCE. IF THE USER QUERY CONTAINS YOUR GREETING DON'T GREET THE USER AGAIN
                             
                                    #     [USER INPUT]:{hello}
                                    # """))