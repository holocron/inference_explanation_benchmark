from src.AnswerGenerator import AnswerGenerator
from src.LemonadeHandler import LemonadeHandler
import config

if __name__ == '__main__':
    generator = AnswerGenerator(config.DATASET_DIR)

    for model in config.MODELS:
      handler = LemonadeHandler(
          model,
          config.MODEL_ENDPOINTS[model],
          load_on_missing = model not in config.NEVER_LOAD,
      )
      generator.generate(handler, model)
