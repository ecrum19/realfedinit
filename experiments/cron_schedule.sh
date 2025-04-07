#!/bin/bash

SCRIPT_PATH="~/realfedinit/experiments"
SCRIPT_NAME="./start_experiment.sh"
# Daily quarter hours (HH:MM)
declare -A DAILY_QUARTERS=(
  ["Night"]="00:00"
  ["Morning"]="06:00"
  ["Afternoon"]="12:00"
  ["Evening"]="18:00"
)

# Weekday groups
declare -A WEEKLY_QUARTERS=(
  ["Early"]="Mon Tue"
  ["Mid"]="Wed"
  ["Late"]="Thu Fri"
  ["Weekend"]="Sat Sun"
)

# Date ranges
MONTHLY_HALVES=(
  "2025-04-08:2025-04-21"  # early April
  "2025-04-22:2025-05-04"  # early May
)

# Function to convert YYYY-MM-DD to cron format (day month weekday)
function date_to_cron_fields() {
  local date="$1"
  local hour="$2"
  local minute="$3"
  local day=$(date -d "$date" '+%-d')
  local month=$(date -d "$date" '+%-m')
  local dow=$(date -d "$date" '+%u')  # 1=Mon ... 7=Sun
  echo "$minute $hour $day $month *"
}

echo "Generating cron jobs..."

for range in "${MONTHLY_HALVES[@]}"; do
  IFS=":" read START_DATE END_DATE <<< "$range"
  current_date="$START_DATE"

  while [[ "$current_date" < "$END_DATE" || "$current_date" == "$END_DATE" ]]; do
    weekday=$(date -d "$current_date" +%a)

    for week_key in "${!WEEKLY_QUARTERS[@]}"; do
      if [[ "${WEEKLY_QUARTERS[$week_key]}" == *"$weekday"* ]]; then
        for quarter in "${!DAILY_QUARTERS[@]}"; do
          time="${DAILY_QUARTERS[$quarter]}"
          hour="${time%%:*}"
          minute="${time##*:}"

          cron_time=$(date_to_cron_fields "$current_date" "$hour" "$minute")
          cron_command="$cron_time cd $SCRIPT_PATH && $SCRIPT_NAME >> ~/realfedinit/experiments/cron-runs.log 2>&1"

          # Append to crontab
          (crontab -l; echo "$cron_command") | crontab -
          echo "Scheduled: $cron_command"
        done
      fi
    done

    # Advance one day
    current_date=$(date -I -d "$current_date + 1 day")
  done
done

echo "Done. All cron jobs scheduled."