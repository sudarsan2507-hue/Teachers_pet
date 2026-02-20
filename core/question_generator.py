import random

class QuestionGenerator:

    def __init__(self):
        self.question_bank = {
            "recursion": [
                "Explain recursion in one sentence.",
                "What is the role of base case in recursion?",
                "Why is base case important in recursive functions?"
            ],
            "sorting": [
                "What is the purpose of sorting algorithms?",
                "Explain how Bubble Sort works in one sentence.",
                "Why is time complexity important in sorting?"
            ],
            "ai": [
                "What is Artificial Intelligence?",
                "What is the difference between ML and AI?",
                "Explain supervised learning in one sentence."
            ]
        }

    def generate_question(self, topic):
        topic = topic.lower()

        if topic in self.question_bank:
            return random.choice(self.question_bank[topic])
        else:
            return f"Explain the concept of {topic} in one sentence."