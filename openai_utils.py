import openai


def generate_prompt(job_description: str, question: str, num_sentences: int = 1) -> str:
    """This function generates a prompt for openai

    Args:
        job_description (str): Job description
        question (str): Question to ask
        num_sentences (int, optional): Length of response in sentences. Defaults to 1.

    Returns:
        str: Prompt for openai

    """
    return f"""Act as a job applicant. Here is a job description: {job_description}
    Give a {num_sentences}-sentence answer to the following question:
    Question: {question}"""


def ask(question: str, job_description: str, num_sentences: int = 1) -> str:
    """This function asks an openai question

    Args:
        question (str): Question to ask
        job_description (str): Job description
        num_sentences (int, optional): Length of response in sentences. Defaults to 1.

    Returns:
        str: Response from openai
    """
    prompt = generate_prompt(job_description, question, num_sentences)
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        temperature=0.9,
        max_tokens=150,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0.6,
        stop=["\n", " User:", " AI:"]
    )
    return response.choices[0].text
