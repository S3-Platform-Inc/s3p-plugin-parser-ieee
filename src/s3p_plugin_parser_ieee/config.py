import datetime

from s3p_sdk.plugin.config import (
    PluginConfig,
    CoreConfig,
    TaskConfig,
    trigger,
    MiddlewareConfig,
    modules,
    payload
)
from s3p_sdk.plugin.types import SOURCE
from s3p_sdk.module import (
    WebDriver,
)

config = PluginConfig(
    plugin=CoreConfig(
        reference='ieee',  # уникальное имя источника
        type=SOURCE,  # Тип источника (SOURCE, ML, PIPELINE)
        files=['ieee.py', ],
        # Список файлов, которые будут использоваться в плагине (эти файлы будут сохраняться в платформе)
        is_localstorage=False
    ),
    task=TaskConfig(
        trigger=trigger.TriggerConfig(
            type=trigger.SCHEDULE,
            interval=datetime.timedelta(days=1),  # Интервал перезапуска плагина
        )
    ),
    middleware=MiddlewareConfig(
        modules=[
            modules.TimezoneSafeControlConfig(order=1, is_critical=True),
            modules.CutJunkCharactersFromDocumentTextConfig(order=2, is_critical=True,
                                                            p_fields=['text', 'abstract']),
            modules.FilterOnlyNewDocumentWithDB(order=3, is_critical=True),
            modules.SaveDocument(order=4, is_critical=True),
        ],
        bus=None,
    ),
    payload=payload.PayloadConfig(
        file='ieee.py',
        # python файл плагина (точка входа). Этот файл должен быть указан в `plugin.files[*]`
        classname='IEEE',  # имя python класса в указанном файле
        entry=payload.entry.EntryConfig(
            method='content',
            params=[
                payload.entry.ModuleParamConfig(key='driver', module_name=WebDriver, bus=True),
                payload.entry.ConstParamConfig(key='max_count_documents', value=50),
                payload.entry.ConstParamConfig(key='url',
                                               value='https://ieeexplore.ieee.org/xpl/tocresult.jsp?isnumber=10005208&punumber=6287639&sortType=vol-only-newest'),
                payload.entry.ConstParamConfig(key='categories',
                                               value=[
                                                   "Computational and artificial intelligence",
                                                   "Computers and information processing",
                                                   "Communications technology",
                                                   "Industry applications",
                                                   "Vehicular and wireless technologies",
                                                   "Systems engineering and theory",
                                                   "Intelligent transportation systems",
                                                   "Information theory",
                                                   "Electronic design automation and methodology",
                                                   "Education",
                                                   "Social implications of technology"
                                               ]),
            ]
        )
    )
)

__all__ = ['config']
