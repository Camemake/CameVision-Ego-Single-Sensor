wget -q -O /tmp/recipe.sh http://192.168.1.44:18765/_recipe.sh
sed -i 's/\r$//' /tmp/recipe.sh
sh /tmp/recipe.sh
