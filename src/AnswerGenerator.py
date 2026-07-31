import os
import json
import copy

class AnswerGenerator:
  def __init__(self, path):
    self.questions_path = path / "questions"
    self.answers_path = path / "answers"
    self.conditions = []

    self._createDirectory(self.answers_path)
    self._listConditions()

  def generate(self, ollama, model_name):
     model_answer_path = self.answers_path / model_name
     self._createDirectory(model_answer_path)
     for condition in self.conditions:
        condition_answer_path = model_answer_path / condition
        condition_question_paths = self._getConditionQuestionPaths(condition)

        self._createDirectory(condition_answer_path)

        for question in condition_question_paths:
          answer = self._answerQuestions(question, ollama)

          file_name = answer['id'] + "_" + condition + ".json"

          with open(condition_answer_path / file_name, 'w') as outfile:
            json.dump(answer, outfile, indent = 2)

  def _answerQuestions(self, question_path, ollama):
    question_data = self._getQuestionData(question_path)
    question_id = question_data["id"]
    template = question_data["template"]
    rules = question_data["rules"]
    concepts = question_data["concepts"]
    init_prompt = question_data["init_prompt"]
    questions = question_data["questions"]

    main_answer_id = "a" + question_id[1:]

    formatted_answer = {}
    formatted_answer["id"] = main_answer_id
    formatted_answer["template"] = template
    formatted_answer["rules"] = rules
    formatted_answer["concepts"] = concepts
    formatted_answer["answers"] = []

    for question in questions:
      formatted_answer["answers"].append(copy.deepcopy(question))
      answer_id = "a" + question['id'][1:]
      formatted_answer["answers"][-1]['id'] = answer_id

      formatted_question = copy.deepcopy(init_prompt)
      formatted_question.append(self._buildCotElem("user", question["question"]))
      formatted_question.append(self._buildCotElem("assistant", "A: Let's translate. translation is "))

      answer, duration = ollama.call(formatted_question)

      formatted_answer["answers"][-1]['answer'] = answer
      formatted_answer["answers"][-1]['duration'] = duration

      print(answer)
    
    return formatted_answer

  def _buildCotElem(self, role, tokens):
    res_elem = {}
    res_elem["role"] = role
    res_elem["content"] = tokens
    return res_elem

  def _getQuestionData(self, path):
    with open(path, 'r') as file:
      data = json.load(file)
      return data

  def _listConditions(self):
    path = self.questions_path
    files = os.listdir(path)
    for file in files:
      if os.path.isdir(os.path.join(path, file)):
        self.conditions.append(file)

  def _getConditionQuestionPaths(self, condition_name):
    path = self.questions_path / condition_name
    result = []
    files = os.listdir(path)
    for file in files:
      full_path = os.path.join(path, file)
      if not os.path.isdir(full_path):
        result.append(full_path)

    return result

  def _createDirectory(self, directory):
    try:
        os.mkdir(directory)
        print(f"Directory '{directory}' created successfully.")
        return True
    except FileExistsError:
        print(f"Directory '{directory}' already exists.")
        return True
    except PermissionError:
        print(f"Permission denied: Unable to create '{directory}'.")
        return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False