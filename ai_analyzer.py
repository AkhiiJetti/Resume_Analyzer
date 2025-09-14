import os
import re
from typing import Dict, List
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

class AIAnalyzer:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found. Please set it in .env")
        
        self.client = Groq(api_key=api_key)
        self.skill_patterns = self._initialize_skill_patterns()

    def _initialize_skill_patterns(self) -> Dict[str, Dict]:
        return {
            'python': {'patterns': ['python', 'py'], 'weight': 1.0, 'category': 'programming_language'},
            'flask': {'patterns': ['flask'], 'weight': 1.0, 'category': 'framework'},
            'django': {'patterns': ['django'], 'weight': 1.0, 'category': 'framework'},
            'rest_api': {'patterns': ['rest api', 'restful api'], 'weight': 1.2, 'category': 'backend_skill'},
            'postgresql': {'patterns': ['postgresql', 'postgres'], 'weight': 1.0, 'category': 'database'},
            'mysql': {'patterns': ['mysql'], 'weight': 1.0, 'category': 'database'},
            'docker': {'patterns': ['docker'], 'weight': 0.8, 'category': 'devops'},
            'aws': {'patterns': ['aws', 'amazon web services'], 'weight': 0.9, 'category': 'cloud'},
            'cloud_deployment': {'patterns': ['azure', 'gcp', 'google cloud', 'heroku'], 'weight': 0.8, 'category': 'cloud'},
            'git': {'patterns': ['git', 'github'], 'weight': 0.7, 'category': 'tools'}
        }

    def analyze_resume_match(self, resume_text: str, job_description: str) -> Dict:
        resume_clean = self._clean_text(resume_text)
        job_clean = self._clean_text(job_description)
        
        resume_skills = self._extract_skills(resume_clean)
        required_skills = self._extract_skills(job_clean)
        
        match_score = self._calculate_match_score(resume_skills, required_skills)
        missing_skills = [s for s in required_skills if s not in resume_skills]
        
        ai_feedback = self._generate_ai_feedback(resume_text, job_description, match_score, missing_skills)
        
        return {
            "matchScore": match_score,
            "presentSkills": list(resume_skills.keys()),
            "missingSkills": missing_skills,
            "suggestions": self._generate_suggestions(missing_skills),
            "aiFeedback": ai_feedback
        }

    def _clean_text(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _extract_skills(self, text: str) -> Dict[str, float]:
        skills_found = {}
        for skill, info in self.skill_patterns.items():
            for pattern in info['patterns']:
                if re.search(r'\b' + re.escape(pattern) + r'\b', text):
                    skills_found[skill] = 1.0
        return skills_found

    def _calculate_match_score(self, resume_skills: Dict[str, float], required_skills: Dict[str, float]) -> int:
        if not required_skills:
            return 0

        total_possible_score = 0.0
        candidate_score = 0.0

    # Calculate the maximum possible score by summing the weights of all skills in the job description
        for skill in required_skills:
            total_possible_score += self.skill_patterns.get(skill, {}).get('weight', 1.0)

    # Find the skills that overlap between the resume and the job description
        overlap_skills = set(resume_skills.keys()) & set(required_skills.keys())

    # Calculate the candidate's score based on the weights of the skills they possess
        for skill in overlap_skills:
            candidate_score += self.skill_patterns.get(skill, {}).get('weight', 1.0)
    
        if total_possible_score == 0:
            return 0

    # Calculate the final percentage based on the weighted scores
        score = int((candidate_score / total_possible_score) * 100)
    
    # --- DEBUGGING PRINT STATEMENTS ---
    # This will print a detailed breakdown to your Flask terminal.
        print("\n--- DEBUGGING SCORE CALCULATION ---")
        print(f"1. Skills found in Job Description : {list(required_skills.keys())}")
        print(f"2. Skills found in Resume         : {list(resume_skills.keys())}")
        print("------------------------------------")
        print(f"3. Overlapping Skills (Matched)    : {list(overlap_skills)}")
        print("------------------------------------")
        print(f"4. Candidate's Weighted Score      : {candidate_score}")
        print(f"5. Total Possible Weighted Score   : {total_possible_score}")
        print("------------------------------------")
        print(f"6. Final Score Calculation         : ({candidate_score} / {total_possible_score}) * 100 = {score}%")
        print("-------------------------------------\n")
    # --- END OF DEBUGGING STATEMENTS ---
    
        return score

    def _generate_suggestions(self, missing_skills: List[str]) -> List[str]:
        return [f"Consider adding or highlighting experience with '{skill}' on your resume." for skill in missing_skills]

    def _generate_ai_feedback(self, resume_text: str, job_description: str, score: int, missing_skills: List[str]) -> str:
        prompt = f"""
        Analyze the following resume against the job description and provide a concise, professional evaluation.
        Resume Snippet: {resume_text[:2000]}
        Job Description Snippet: {job_description[:2000]}
        The resume has a keyword match score of {score}%.
        The following keywords from the job description appear to be missing from the resume: {', '.join(missing_skills) if missing_skills else 'None'}.
        Based on this, provide a 3-part analysis in markdown format:
        1. Strengths: Briefly mention 2-3 strong points of the resume in relation to the job.
        2. Areas for Improvement: Suggest 2-3 areas where the resume could be better aligned with the job description.
        3. Overall Recommendation: A concluding sentence about the candidate's fit.
        """
        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400,
                temperature=0.5
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"An error occurred with Groq API: {e}")
            return "Could not generate AI feedback due to a server error. Please check the backend logs for details."