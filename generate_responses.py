from src.AnswerGenerator import AnswerGenerator
import config

if __name__ == '__main__':
    generator = AnswerGenerator(config.DATASET_DIR)

    if config.BACKEND == "lemonade":
      from src.LemonadeHandler import LemonadeHandler
      handlers = {model: LemonadeHandler(model, config.LEMONADE_BASE_URL) for model in config.MODELS}
    else:
      from src.OllamaHandler import OllamaHandler
      handlers = {model: OllamaHandler(model) for model in config.MODELS}

    for model in config.MODELS:
      generator.generate(handlers[model], model)
