# Послідовність виконання

Linux-частину виконано у Debian 12 ARM64 з реальним systemd PID 1 у контейнері Docker Desktop.
Команди journalctl, systemctl, iostat, lsblk та fdisk виконуються у Linux; показані диски належать віртуальній машині Docker, а не фізичній таблиці розділів macOS.

## 1. Підготовка Linux

```bash
bash scripts/start_linux.sh
bash scripts/linux.sh ps -p 1 -o comm=
bash scripts/linux.sh systemctl is-active systemd-journald ssh mytest
```

Контейнер використовує окремий cgroup namespace; системні каталоги macOS у нього не монтуються.
Привілейований режим потрібен для запуску systemd у цьому навчальному контейнері.

## 2. Журнали

Увійти до Linux:

```bash
bash scripts/linux.sh
cd /work
journalctl -n 10 --no-pager -o short-iso > logs.txt
journalctl -u ssh.service --no-pager -o short-iso > sshd-logs.txt
```

У Debian демон `sshd` належить юніту `ssh.service`; тому фільтр журналу використовує саме цю назву.

## 3. I/O та диски

```bash
/opt/lab-venv/bin/python scripts/measure_io.py
lsblk /dev/vda /dev/vdb -o NAME,SIZE,TYPE,MOUNTPOINTS
fdisk -l /dev/vda
```

`iostat -d -y vda 1 2` дає дві секундні вибірки без середнього з моменту завантаження.
Поле `tps` показує передачі I/O за секунду (спостережувані IOPS); `kB_read/s` і `kB_wrtn/s` — пропускну здатність читання та запису.
Це поточне навантаження віртуального диска, не його максимальна продуктивність.
Сценарій створює обмежене навантаження: чотири записи по 16 MiB у власний тимчасовий файл, після чого видаляє його.

IOPS рахують операції, а пропускна здатність — обсяг даних за секунду; зв'язок залежить від розміру операцій.
Сучасний `fdisk` підтримує GPT і MBR, але орієнтований на діалогову роботу; `parted` має сценарний режим `-s` і пряму команду `resizepart` для зміни кінця існуючого розділу.
`resizepart` не змінює розмір файлової системи; у цій роботі таблиці розділів лише читалися.

## 4. systemd

```bash
systemctl status mytest.service --no-pager
journalctl -u mytest.service -n 4 --no-pager
tail -n 3 /tmp/test.log
```

Юніт і сценарій зберігаються у `linux/`; Dockerfile встановлює їх у `/etc/systemd/system/` та `/opt/mytest/`.
`WorkingDirectory=/opt/mytest` задає поточний каталог процесу й базу для відносних шляхів; абсолютний `/tmp/test.log` від нього не залежить.
`heartbeat.sh` пише перший рядок одразу, далі — кожні 60 секунд, і дублює його в journal через stdout.

## 5. Збірка Python-пакета

У Linux встановіть інструменти в окремий venv:

```bash
/opt/lab-venv/bin/python -m pip install -r requirements-lab.txt
export PATH=/opt/lab-venv/bin:$PATH
cd /work
bash scripts/build_package.sh
```

`python -m build` створює wheel і sdist у `dist/`; `twine check` перевіряє їхні метадані.
Код пакета — `src/study5_hello/`, конфігурація — `pyproject.toml`.

## 6. Локальний PyPI і встановлення

```bash
python scripts/setup_devpi.py
python scripts/upload_package.py
bash scripts/install_package.sh
```

`setup_devpi.py` ініціалізує devpi, запускає його systemd-юніт і створює індекс `student/lab` без успадкування зовнішнього PyPI.
Випадковий пароль та стан клієнта залишаються у контейнері поза `/work`; вони не входять до GitHub або архіву.
Twine отримує пароль через змінну середовища й завантажує файли на `http://127.0.0.1:3141/student/lab/`.
Для pip використовується інший endpoint: `http://127.0.0.1:3141/student/lab/+simple/`.
Перевірка створює свіжий venv `/opt/study5-verify`, вимикає кэш і залежності та запускає модуль з `/tmp` у режимі `-I`, щоб не імпортувати локальні вихідні файли.

## 7. .deb, .rpm і CHANGELOG

| Ознака | .deb | .rpm |
| --- | --- | --- |
| Інструменти | dpkg / APT | RPM / DNF |
| Структура | ar із control.tar та data.tar | Заголовки й payload cpio |
| Опис залежностей | control: Depends | SPEC: Requires |

`CHANGELOG.md` містить версію 0.1.0, дату 2026-10-28 та секції Added / Fixed / Security.
Changelog пов'язує версію зі змінами, допомагає оцінити реліз, перевірити розгортання й обрати версію для відкату.
Для початкового релізу відсутність виправлень і змін безпеки вказана прямо.

## 8. Molotov

```bash
install -m 644 /work/linux/json-server.service /etc/systemd/system/json-server.service
systemctl daemon-reload
systemctl enable --now json-server.service
curl -i http://127.0.0.1:8085/
bash scripts/load_test.sh
```

Сценарій `loadtest.py` перевіряє HTTP 200, JSON-об'єкт і поле `status=ok`.
Тест обмежений двома workers, трьома секундами та 50 запусками на worker; перша невдала перевірка спричиняє ненульовий код завершення.
Параметр `-c` вмикає простий консольний вивід, `-w 2` задає кількість workers.

## 9. GitHub та матеріали

Репозиторій: https://github.com/mag871498-sys/independent-5-linux-pypi

Після кожного етапу створено окремий змістовний коміт; початковий пароль devpi й машинні SSH-ключі не публікуються.
Скриншоти у звіті — справжні знімки Terminal; для завершених операцій збірки й завантаження показано збережений фактичний вивід.
Для зупинки власної навчальної Linux-системи виконайте на Mac `docker compose stop` у папці проєкту; повторний запуск — `docker compose start`.

## Первинні джерела

- [journalctl](https://www.freedesktop.org/software/systemd/man/latest/journalctl.html)
- [WorkingDirectory](https://www.freedesktop.org/software/systemd/man/latest/systemd.exec.html)
- [fdisk](https://manpages.debian.org/bookworm/fdisk/fdisk.8.en.html)
- [GNU Parted resizepart](https://www.gnu.org/software/parted/manual/html_node/resizepart.html)
- [devpi quickstart](https://github.com/devpi/devpi/blob/main/doc/quickstart-releaseprocess.rst)
- [Python Packaging Guide](https://packaging.python.org/en/latest/tutorials/packaging-projects/)
- [Molotov](https://molotov.readthedocs.io/en/stable/)
