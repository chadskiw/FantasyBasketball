$(document).ready(function () {
    const dailyScheduleChartCtx = document.getElementById('daily-schedule-chart').getContext('2d');
    const dailyScheduleChart = new Chart(dailyScheduleChartCtx, {
        type: 'bar',
        data: {
            labels: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            datasets: [
                {
                    label: 'Total Points',
                    type: 'bar',
                    backgroundColor: 'rgba(255, 99, 132, 0.6)',
                    borderColor: 'rgba(255, 99, 132, 1)',
                    borderWidth: 1,
                    data: [0, 0, 0, 0, 0, 0, 0],
                },
                {
                    label: '# of Players',
                    type: 'line',
                    fill: false,
                    backgroundColor: 'rgba(75, 192, 192, 0.6)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 2,
                    data: [0, 0, 0, 0, 0, 0, 0],
                },
            ],
        },
        options: {
            responsive: true,
        },
    });

    const suggestedPickupsTable = $('#suggested-pickups').DataTable();
    const dropCandidatesTable = $('#drop-candidates').DataTable();

    $('#team-week-form').on('submit', async function (e) {
        e.preventDefault();
        const week = $('#week').val();
        const team = $('#team').val();

        try {
            const response = await fetch('/recommendations', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ week, team }),
            });

            if (!response.ok) throw new Error('Failed to fetch recommendations');
            const data = await response.json();

            // Populate Suggested Pickups
            suggestedPickupsTable.clear();
            data.suggested_pickups.forEach(player => {
                suggestedPickupsTable.row.add([
                    `<input type="checkbox" class="player-checkbox" data-game-days="${player.game_days}" data-points="${player.average_points}">`,
                    player.name,
                    player.status,
                    player.position,
                    player.team,
                    player.games_in_week,
                    player.average_points.toFixed(2),
                    (player.games_in_week * player.average_points).toFixed(2),
                    player.game_days,
                ]).draw();
            });

            // Populate Drop Candidates
            dropCandidatesTable.clear();
            data.drop_candidates.forEach(player => {
                dropCandidatesTable.row.add([
                    `<input type="checkbox" class="player-checkbox" data-game-days="${player.game_days}" data-points="${player.average_points}">`,
                    player.name,
                    player.status,
                    player.position,
                    player.team,
                    player.games_in_week,
                    player.average_points.toFixed(2),
                    (player.games_in_week * player.average_points).toFixed(2),
                    player.game_days,
                ]).draw();
            });

            // Update chart data and totals
            updateChartDataAndTotalPoints();

        } catch (error) {
            console.error('Error fetching recommendations:', error);
            alert('Failed to fetch recommendations. Please try again.');
        }
    });
});