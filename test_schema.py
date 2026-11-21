
from pydantic import ValidationError
from schemas import Resume

valid_data = {
    "name": "Rahul Sharma",
    "email": "rahul@example.com",
    "phone": "+91 9876543210",
    "skills": ["Python", "SQL"],
    "experience_years": 3,
    "education": "B.Tech"
}

invalid_data = {
    "name": "Rahul Sharma",
    "email": "wrong-email",
    "phone": None,
    "skills": "Python",
    "experience_years": -3,
    "education": None
}

print("TEST 1: Valid resume")

resume = Resume.model_validate(valid_data)
print(resume.model_dump_json(indent=2))

print("\nTEST 2: Invalid resume")

try:
    Resume.model_validate(invalid_data)

except ValidationError as error:
    for issue in error.errors():
        print("Field:", issue["loc"])
        print("Problem:", issue["msg"])
        print()
