#!/bin/bash
commands='17'

RED='\033[1;91m'
CYAN='\033[1;96m'
PURPLE_LIGHT='\033[5;35m'
RESET='\033[0m'

start_process_line="${PURPLE_LIGHT}################################################################################"
end_process_line="################################################################################${RESET}"

logo="\e[38;5;0m.\e[0m\e[38;5;0m.\e[0m\e[38;5;0m.\e[0m\e[38;5;0m.\e[0m\e[38;5;0m.\e[0m\e[38;5;0m.\e[0m\e[38;5;0m.\e[0m\e[38;5;0m.\e[0m\e[38;5;0m.\e[0m\e[38;5;0m.\e[0m\e[38;5;0m.\e[0m\e[38;5;0m.\e[0m\e[38;5;0m.\e[0m\e[38;5;0m.\e[0m\e[38;5;0m.\e[0m\e[38;5;0m.\e[0m\e[38;5;0m.\e[0m\e[38;5;0m.\e[0m\e[38;5;0m.\e[0m\e[38;5;0m.\e[0m\e[38;5;0m.\e[0m\e[38;5;0m.\e[0m
\e[38;5;0m.\e[0m\e[38;5;0m.\e[0m\e[38;5;52m>\e[0m\e[38;5;88m|\e[0m\e[38;5;124m}\e[0m\e[38;5;124m]\e[0m\e[38;5;124m]\e[0m\e[38;5;88m?\e[0m\e[38;5;88m?\e[0m\e[38;5;124m+\e[0m\e[38;5;124m+\e[0m\e[38;5;124m+\e[0m\e[38;5;124m+\e[0m\e[38;5;88m?\e[0m\e[38;5;88m?\e[0m\e[38;5;124m]\e[0m\e[38;5;124m]\e[0m\e[38;5;124m]\e[0m\e[38;5;88m|\e[0m\e[38;5;52m>\e[0m\e[38;5;0m.\e[0m\e[38;5;0m.\e[0m
\e[38;5;0m.\e[0m\e[38;5;0m'\e[0m\e[38;5;15mP\e[0m\e[38;5;15mL\e[0m\e[38;5;15mA\e[0m\e[38;5;15mY\e[0m\e[38;5;15mE\e[0m\e[38;5;15mR\e[0m\e[38;5;15mO\e[0m\e[38;5;15mK\e[0m\e[38;5;0m \e[0m\e[38;5;15mC\e[0m\e[38;5;15mA\e[0m\e[38;5;15mR\e[0m\e[38;5;15mD\e[0m\e[38;5;15mI\e[0m\e[38;5;15mN\e[0m\e[38;5;15mA\e[0m\e[38;5;15mL\e[0m\e[38;5;0m'\e[0m\e[38;5;0m.\e[0m
\e[38;5;0m.\e[0m\e[38;5;0m.\e[0m\e[38;5;52m>\e[0m\e[38;5;88m|\e[0m\e[38;5;124m]\e[0m\e[38;5;124m]\e[0m\e[38;5;124m+\e[0m\e[38;5;88m?\e[0m\e[38;5;88m?\e[0m\e[38;5;124m+\e[0m\e[38;5;124m+\e[0m\e[38;5;124m+\e[0m\e[38;5;124m+\e[0m\e[38;5;88m?\e[0m\e[38;5;88m?\e[0m\e[38;5;124m+\e[0m\e[38;5;124m]\e[0m\e[38;5;124m]\e[0m\e[38;5;88m|\e[0m\e[38;5;52m>\e[0m\e[38;5;0m.\e[0m\e[38;5;0m.\e[0m
\e[38;5;0m.\e[0m\e[38;5;0m.\e[0m\e[38;5;0m.\e[0m\e[38;5;0m.\e[0m\e[38;5;0m.\e[0m\e[38;5;0m.\e[0m\e[38;5;0m.\e[0m\e[38;5;0m.\e[0m\e[38;5;0m.\e[0m\e[38;5;0m.\e[0m\e[38;5;0m.\e[0m\e[38;5;0m.\e[0m\e[38;5;0m.\e[0m\e[38;5;0m.\e[0m\e[38;5;0m.\e[0m\e[38;5;0m.\e[0m\e[38;5;0m.\e[0m\e[38;5;0m.\e[0m\e[38;5;0m.\e[0m\e[38;5;0m.\e[0m\e[38;5;0m.\e[0m\e[38;5;0m.\e[0m"

clear
echo -e $logo

echo -e "\n\n${RED} * GitHub ${CYAN}github.com/KITUSTTT/PlayerokCardinal${RESET}"
echo -e "${RED} * Telegram ${CYAN}t.me/KaDerix${RESET}"
echo -e "\n\n\n"

echo -ne "${CYAN}Введите имя пользователя, от имени которого будет запускаться бот (например, 'poc' или 'cardinal'): ${RESET}"
while true; do
  read username
  if [[ "$username" =~ ^[a-zA-Z][a-zA-Z0-9_-]+$ ]]; then
    if id "$username" &>/dev/null; then
      echo -ne "\n${RED}Такой пользователь уже существует. ${CYAN}Пожалуйста, введите другое имя пользователя: ${RESET}"
    else
      break
    fi
  else
    echo -ne "\n${RED}Имя пользователя содержит недопустимые символы. ${CYAN}Имя должно начинаться с буквы и может включать только буквы, цифры, '_', или '-'. Пожалуйста, введите другое имя пользователя: ${RESET}"
  fi
done

distro_version=$(lsb_release -rs)

clear
echo -e "${start_process_line}\nДобавляю репозитории...\n${end_process_line}"

if ! sudo apt update ; then
  echo -e "${start_process_line}\nПроизошла ошибка при обновлении списка пакетов. (1/${commands})\n${end_process_line}"
  exit 2
fi

if ! sudo apt install -y software-properties-common ; then
  echo -e "${start_process_line}\nПроизошла ошибка при установке software-properties-common. (2/${commands})\n${end_process_line}"
  exit 2
fi

case $distro_version in
  "22.04" | "22.10" | "23.04" | "23.10" | "24.04" | "24.10")
    ;;
  "12")
    ;;
  "11")
    if ! sudo apt install -y gnupg ; then
      echo -e "${start_process_line}\nПроизошла ошибка при установке gnupg. (3.1/${commands})\n${end_process_line}"
      exit 2
    fi

    if ! sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys BA6932366A755776 ; then
      echo -e "${start_process_line}\nПроизошла ошибка при добавлении ключа репозитория. (3.2/${commands})\n${end_process_line}"
      exit 2
    fi

    if ! sudo add-apt-repository -s "deb https://ppa.launchpadcontent.net/deadsnakes/ppa/ubuntu focal main" ; then
      echo -e "${start_process_line}\nПроизошла ошибка при добавлении репозитория. (3.3/${commands})\n${end_process_line}"
      exit 2
    fi

    sudo tee /etc/apt/preferences.d/10deadsnakes-ppa >/dev/null <<EOF
Package: *
Pin: release o=LP-PPA-deadsnakes
Pin-Priority: 100
EOF
    if $? -ne 0 ; then
      echo -e "${start_process_line}\nПроизошла ошибка при добавлении приоритета репозитория. (3.4/${commands})\n${end_process_line}"
      exit 2
    fi
    ;;
  *)
    if ! sudo add-apt-repository -y ppa:deadsnakes/ppa ; then
      echo -e "${start_process_line}\nПроизошла ошибка при добавлении репозитория. (3/${commands})\n${end_process_line}"
      exit 2
    fi
    ;;
esac

if ! sudo apt update ; then
  echo -e "${start_process_line}\nПроизошла ошибка при обновлении списка пакетов. (4/${commands})\n${end_process_line}"
  exit 2
fi

clear
echo -e "$start_process_line\nУстанавливаю необходимые пакеты...\n$end_process_line"

if ! sudo apt install -y curl ; then
  echo -e "${start_process_line}\nПроизошла ошибка при установке Curl. (5/${commands})\n${end_process_line}"
  exit 2
fi

if ! sudo apt install -y unzip ; then
  echo -e "${start_process_line}\nПроизошла ошибка при установке Unzip. (6/${commands})\n${end_process_line}"
  exit 2
fi

clear
echo -e "$start_process_line\nУстанавливаю Python...\n$end_process_line"

case $distro_version in
  "24.04" | "24.10")
    if ! sudo apt install -y python3.12 python3.12-dev python3.12-gdbm python3.12-venv ; then
      echo -e "${start_process_line}\nПроизошла ошибка при установке Python. (7/${commands})\n${end_process_line}"
      exit 2
    fi
    ;;
  *)
    if ! sudo apt install -y python3.11 python3.11-dev python3.11-gdbm python3.11-venv ; then
      echo -e "${start_process_line}\nПроизошла ошибка при установке Python. (7/${commands})\n${end_process_line}"
      exit 2
    fi
    ;;
esac

clear
echo -e "$start_process_line\nСоздаю пользователя и устанавливаю/обновляю Pip...\n$end_process_line"

if ! sudo useradd -m $username ; then
  echo -e "${start_process_line}\nПроизошла ошибка при создании пользователя. (8/${commands})\n${end_process_line}"
  exit 2
fi

case $distro_version in
  "24.04" | "24.10")
    if ! sudo -u $username python3.12 -m venv /home/$username/pyvenv ; then
      echo -e "${start_process_line}\nПроизошла ошибка при создании виртуального окружения. (9/${commands})\n${end_process_line}"
      exit 2
    fi
    ;;
  *)
    if ! sudo -u $username python3.11 -m venv /home/$username/pyvenv ; then
      echo -e "${start_process_line}\nПроизошла ошибка при создании виртуального окружения. (9/${commands})\n${end_process_line}"
      exit 2
    fi
    ;;
esac

if ! sudo /home/$username/pyvenv/bin/python -m ensurepip --upgrade ; then
  echo -e "${start_process_line}\nПроизошла ошибка при установке Pip. (10/${commands})\n${end_process_line}"
  exit 2
fi

if ! sudo -u $username /home/$username/pyvenv/bin/python -m pip install --upgrade pip ; then
  echo -e "${start_process_line}\nПроизошла ошибка при обновлении Pip. (11/${commands})\n${end_process_line}"
  exit 2
fi

if ! sudo chown -hR $username:$username /home/$username/pyvenv ; then
  echo -e "${start_process_line}\nПроизошла ошибка при изменении владельца виртуального окружения. (12/${commands})\n${end_process_line}"
  exit 2
fi

clear
echo -e "$start_process_line\nУстанавливаю PlayerokCardinal...\n$end_process_line"

if ! sudo apt install -y git ; then
  echo -e "${start_process_line}\nПроизошла ошибка при установке Git. (13/${commands})\n${end_process_line}"
  exit 2
fi

gh_repo="KITUSTTT/PlayerokCardinal"

if ! sudo -u $username git clone https://github.com/${gh_repo}.git /home/$username/PlayerokCardinal ; then
  echo -e "${start_process_line}\nПроизошла ошибка при клонировании репозитория. (14/${commands})\n${end_process_line}"
  exit 2
fi

if ! sudo -u $username /home/$username/pyvenv/bin/pip install -U -r /home/$username/PlayerokCardinal/requirements.txt ; then
  echo -e "${start_process_line}\nПроизошла ошибка при установке необходимых Py-пакетов. (15/${commands})\n${end_process_line}"
  exit 2
fi

clear
echo -e "$start_process_line\nСоздаю ссылку на файл фонового процесса...\n$end_process_line"

if ! sudo ln -sf /home/$username/PlayerokCardinal/PlayerokCardinal@.service /etc/systemd/system/PlayerokCardinal@.service ; then
  echo -e "${start_process_line}\nПроизошла ошибка при создании ссылки на файл фонового процесса. (16/${commands})\n${end_process_line}"
  exit 2
fi

clear
echo -e "$start_process_line\nНастраиваю кодировку сервера...\n$end_process_line"

case $distro_version in
  "11" | "12")
    if ! sudo apt install -y locales locales-all ; then
      echo -e "${start_process_line}\nПроизошла ошибка при установке локализаций. (17/${commands})\n${end_process_line}"
      exit 2
    fi
    ;;
  *)
    if ! sudo apt install -y language-pack-en ; then
      echo -e "${start_process_line}\nПроизошла ошибка при установке языковых пакетов. (17/${commands})\n${end_process_line}"
      exit 2
    fi
    ;;
esac

clear
echo -e $logo
echo -e '\n\n\e[1;91m * GitHub \e[1;96mgithub.com/KITUSTTT/PlayerokCardinal\e[0m'
echo -e '\e[1;91m * Telegram \e[1;96mt.me/KaDerix\e[0m'

echo -e "\n\n\e[1;92m################################################################################"
echo -e "Установка завершена."
echo -e "Запускаю первичную настройку..."
echo -e "################################################################################\e[0m"
sleep 3
clear

echo -e "\n${CYAN}Starting first setup. Please answer all questions...${RESET}\n"
sleep 2

cd /home/$username/PlayerokCardinal

su - $username -c "cd /home/$username/PlayerokCardinal && LANG=en_US.utf8 /home/$username/pyvenv/bin/python main.py"

echo -e "\n${GREEN}First setup completed! Starting bot as service...${RESET}\n"
sleep 2

sudo systemctl daemon-reload
sudo systemctl start PlayerokCardinal@$username.service

clear
echo -e $logo
echo -e '\n\n\e[1;91m * GitHub \e[1;96mgithub.com/KITUSTTT/PlayerokCardinal\e[0m'
echo -e '\e[1;91m * Telegram \e[1;96mt.me/KaDerix\e[0m'

echo -e "\n\n\e[1;92m################################################################################"
echo -e "${RED}!СДЕЛАЙ СКРИНШОТ!${CYAN}!СДЕЛАЙ СКРИНШОТ!${RED}!СДЕЛАЙ СКРИНШОТ!${CYAN}!СДЕЛАЙ СКРИНШОТ!"
echo -e "\nГотово!"
echo -e "POC запущен как фоновый процесс!"
echo -e "Теперь напиши своему Telegram-боту."
echo -e "\n\e[1;92mДля остановки POC используй команду \e[93msudo systemctl stop PlayerokCardinal@${username}\e[1;92m"
echo -e "Для запуска POC используй команду \e[93msudo systemctl start PlayerokCardinal@${username}\e[1;92m"
echo -e "Для перезапуска POC используй команду \e[93msudo systemctl restart PlayerokCardinal@${username}\e[1;92m"
echo -e "Для просмотра логов используй команду \e[93msudo systemctl status PlayerokCardinal@${username} -n100\e[1;92m"
echo -e "Для добавления POC в автозагрузку используй команду \e[93msudo systemctl enable PlayerokCardinal@${username}\e[1;92m"
echo -e "${RED}* Перед добавлением POC в автозагрузку убедись, что твой бот работает корректно.\e[1;92m"
echo -e "################################################################################\e[0m"

echo -ne "\n\n${CYAN}Сделал скриншот? ${PURPLE_LIGHT}Тогда нажми Enter, чтобы продолжить.${RESET}"
read
clear

