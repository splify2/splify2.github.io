# Быстрый старт

Все команды выполняются на роутере по ssh (`ssh root@192.168.1.1`). Архитектуру и менеджер пакетов
(apk на OpenWrt 25.12, opkg на более старых) установщики определяют сами — их видно в
`/etc/openwrt_release`, строки `DISTRIB_ARCH` и `DISTRIB_RELEASE`.

## Панель splify2 с ядром

```sh
wget -O /tmp/splify2-install.sh https://gitlab.com/xyzmean/splify2/-/raw/main/install.sh && sh /tmp/splify2-install.sh
```

Ссылка ведёт на зеркало GitLab: оно открывается и там, где закрыт `githubusercontent.com`. Если
файл всё же не скачался, установщик и всё, что роутер берёт из интернета, пробует прямой адрес,
зеркало и запасные хосты GitHub по очереди.

После установки откройте LuCI → **Сервисы → splify2**:

1. **VPN** — добавьте выход: готовый интерфейс роутера (WireGuard, AmneziaWG), подписку VLESS или
   hysteria2, интерфейс xsteer.
2. **Правила** — выберите сервисы из каталога и выход для них.
3. **Главная** — состояние выходов и правил, поле «Куда пойдёт запрос» показывает, по какому
   правилу уйдёт имя.

Удалить всё, что поставила панель: `splify2-purge` покажет план, `splify2-purge --yes` выполнит его.

## Ядро steer отдельно

Пакеты берутся со страницы [выпусков steer](https://github.com/splify2/steer/releases): ядро
`steer-core` нужно всегда, модули протоколов — по нужде (`steer-vless`, `steer-hysteria2`,
`steer-proxy`, `steer-xsteer`, `steer-obfs`, `steer-tgws`). Все одной версии и одной архитектуры,
одной командой:

```sh
# OpenWrt на apk
apk add --allow-untrusted ./steer-core-<версия>-1_<арх>.apk ./steer-vless-<версия>-1_<арх>.apk
# OpenWrt на opkg
opkg install ./steer-core-<версия>-1_<арх>.ipk ./steer-vless-<версия>-1_<арх>.ipk
```

Минимальная спека `/etc/steer/spec.yaml` — домены из списка через WireGuard, остальное напрямую:

```yaml
version: 2
lan: { devices: [br-lan] }
lists:
  blocked: { domains_file: lists/blocked.dom }
outputs:
  vpn: { kind: interface, device: wg0, on_fail: drop }
rules:
  - { name: блоклист, to: [blocked], out: vpn }
```

```sh
steer apply --dry-run      # что получится, ничего не применяя
steer apply                # применить
steer status               # что стоит сейчас
steer diag                 # что сломано и почему
steer explain example.org  # какое правило и выход достанутся имени
```

Списки — текстовые файлы по записи на строку: `example.org`, `*.example.org`, адреса и подсети в
`prefixes_file`. Ядро списки не скачивает, а читает то, что ему положили. Все ключи спеки — в
[справочнике](/docs/steer/spec-v2/).

## Коннектор для podkop и forkop

Если на роутере уже работает podkop или forkop, их можно оставить и заменить только `sing-box`:

```sh
tar -xzf steer-box-connector-test-<версия>.tar.gz
cd steer-box-connector-test-<версия>
sh install.sh
```

Подробности — на странице [коннектора](/docs/connector/).
