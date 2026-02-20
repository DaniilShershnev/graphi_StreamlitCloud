import yaml   # импортируем библиотеку для парсинга .yaml файлов



def load_config(config_path):
    with open(config_path, 'r', encoding='utf-8') as f:  #пишем with open, потому что with автоматически закрывает файл. Без with пришлось бы писать такой код: f = open(config_path, 'r')
        #  config = yaml.safe_load(f)       f.close()
        config = yaml.safe_load(f)
    return config


def load_batch_configs(batch_path):
    with open(batch_path, 'r', encoding='utf-8') as f:
        batch = yaml.safe_load(f)

    configs = []
    for config_file in batch['configs']:
        config = load_config(config_file)
        configs.append(config)

    return configs