echo "🔍 Проверка сетевых подключений между контейнерами..."

containers=("mcp_github" "mcp_web_search" "mcp_sheets" "db" "redis")

for container in "${containers[@]}"; do
    echo "Проверка контейнера: $container"
    if docker exec hr_assistant_app nc -z $container 8001 2>/dev/null; then
        echo "✅ $container доступен"
    else:
        echo "❌ $container НЕ доступен"
    fi
done
