import React, { useState, useEffect } from 'react';
import { PieChart, Pie, Cell, Tooltip } from 'recharts';
import './App.css';

function App() {
  const [steamId, setSteamId] = useState('');
  const [recentGames, setRecentGames] = useState([]);
  const [allGames, setAllGames] = useState([]);
  const [displayMode, setDisplayMode] = useState('hours'); // "hours", "minutes", "percentage"
  const [loading, setLoading] = useState(false);
  const [darkMode, setDarkMode] = useState(true);
  const [totalPlaytime, setTotalPlaytime] = useState(0);

  const fetchRecentGames = () => {
    setLoading(true);
    fetch(`http://localhost:5000/steam/recently_played/${steamId}`)
      .then(response => response.json())
      .then(data => {
        setRecentGames(data);
      })
      .catch(error => console.error('Error fetching recent games:', error))
      .finally(() => setLoading(false));
  };

  const fetchAllGamesGenres = () => {
    setLoading(true);
    fetch(`http://localhost:5000/steam/all_games_genres/${steamId}`)
      .then(response => response.json())
      .then(data => {
        setAllGames(data);

        // Calculate the total playtime of all games
        const total = data.reduce((sum, game) => sum + game.playtime_forever, 0);
        setTotalPlaytime(total);
      })
      .catch(error => console.error('Error fetching all games genres:', error))
      .finally(() => setLoading(false));
  };

  // Prepare data for the pie chart based on playtime per genre
  const genreData = allGames.reduce((acc, game) => {
    game.genres.forEach(genre => {
      const found = acc.find(item => item.name === genre);
      const playtime = game.playtime_forever;

      if (found) {
        if (displayMode === 'hours') {
          found.value += playtime / 60; // Convert minutes to hours
        } else if (displayMode === 'minutes') {
          found.value += playtime;
        } else if (displayMode === 'percentage') {
          found.value += (playtime / totalPlaytime) * 100; // Calculate percentage of total time
        }
      } else {
        acc.push({
          name: genre,
          value:
            displayMode === 'hours' ? playtime / 60 :
            displayMode === 'minutes' ? playtime :
            (playtime / totalPlaytime) * 100 // Initialize with appropriate value
        });
      }
    });
    return acc;
  }, []);

  // Sort genre data by descending playtime
  genreData.sort((a, b) => b.value - a.value);

  const COLORS = [
    '#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#9900FF',
    '#E6194B', '#3CB44B', '#FFE119', '#4363D8', '#F58231',
    '#911EB4', '#46F0F0', '#F032E6', '#BCF60C', '#FABEBE',
    '#008080', '#E6BEFF', '#9A6324', '#FFFAC8', '#800000'
  ];

  useEffect(() => {
    if (steamId) {
      fetchRecentGames();
      fetchAllGamesGenres();
    }
  }, [steamId]);  // Fetch data when steamId changes

  return (
    <div className={`App ${darkMode ? 'dark-mode' : 'light-mode'}`} style={{ backgroundColor: darkMode ? '#121212' : '#ffffff', color: darkMode ? '#ffffff' : '#000000' }}>
      <header className="App-header" style={{ backgroundColor: darkMode ? '#1e1e1e' : '#ffffff', boxShadow: darkMode ? '0 2px 10px rgba(0, 0, 0, 0.7)' : '0 2px 10px rgba(0, 0, 0, 0.1)' }}>
        
        <input
          type="text"
          value={steamId}
          onChange={e => setSteamId(e.target.value)}
          placeholder="Enter Steam ID"
          style={{ backgroundColor: darkMode ? '#333333' : '#ffffff', color: darkMode ? '#ffffff' : '#000000' }}
        />
        <button onClick={() => { fetchRecentGames(); fetchAllGamesGenres(); }} style={{ backgroundColor: darkMode ? '#444444' : '#007bff', color: darkMode ? '#ffffff' : '#ffffff' }}>Fetch Games</button>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', justifyContent: 'center', marginTop: '10px' }}>
          <label>
            <input
              type="checkbox"
              checked={darkMode}
              onChange={() => setDarkMode(!darkMode)}
            />
            Dark Mode
          </label>
          <label>
            Display Mode:
            <select value={displayMode} onChange={e => setDisplayMode(e.target.value)} style={{ marginLeft: '10px' }}>
              <option value="hours">Hours</option>
              <option value="minutes">Minutes</option>
              <option value="percentage">Percentage</option>
            </select>
          </label>
        </div>

        <div className="TotalPlaytime" style={{ marginTop: '20px', backgroundColor: darkMode ? '#1e1e1e' : '#ffffff', padding: '10px', borderRadius: '8px' }}>
          <h2>Total Playtime Across All Games</h2>
          <p>
            {
              displayMode === 'minutes' ? totalPlaytime :
              displayMode === 'percentage' ? '100%' :
              (totalPlaytime / 60).toFixed(2) + ' hours'
            }
          </p>
        </div>

        <div className="TopGames-container" style={{ display: 'flex', justifyContent: 'space-between', marginTop: '20px', width: '100%' }}>
          <div className="TopGames-list-container" style={{ width: '48%' }}>
            <h2>Top Played Games in Last Two Weeks</h2>
            <div className="TopGames-list" style={{ backgroundColor: darkMode ? '#1e1e1e' : '#ffffff', padding: '10px', borderRadius: '8px', height: '135px', overflowY: 'scroll' }}>
              <ul style={{ listStyle: 'none', padding: '0', margin: '0' }}>
                {recentGames.length > 0 ? (
                  recentGames.map(game => {
                    const playtime = displayMode === 'hours' ? (game.playtime_2weeks / 60).toFixed(2) :
                      displayMode === 'minutes' ? game.playtime_2weeks :
                      ((game.playtime_2weeks / totalPlaytime) * 100).toFixed(2);

                    const unit = displayMode === 'percentage' ? '%' : (displayMode === 'hours' ? 'hours' : 'minutes');
                    
                    return (
                      <li key={game.appid} style={{ backgroundColor: darkMode ? '#2e2e2e' : '#f8f9fa', padding: '10px', margin: '5px 0', borderRadius: '4px' }}>
                        {game.name} - {playtime} {unit}
                      </li>
                    );
                  })
                ) : (
                  <li style={{ backgroundColor: darkMode ? '#2e2e2e' : '#f8f9fa', padding: '10px', margin: '5px 0', borderRadius: '4px' }}>No games played recently</li>
                )}
              </ul>
            </div>
          </div>
          <div className="TopGames-list-container" style={{ width: '48%' }}>
            <h2>Top Played Games of All Time</h2>
            <div className="TopGames-list" style={{ backgroundColor: darkMode ? '#1e1e1e' : '#ffffff', padding: '10px', borderRadius: '8px', height: '135px', overflowY: 'scroll' }}>
              <ul style={{ listStyle: 'none', padding: '0', margin: '0' }}>
                {allGames.length > 0 ? (
                  allGames
                    .sort((a, b) => b.playtime_forever - a.playtime_forever)
                    .map(game => {
                      const playtime = displayMode === 'hours' ? (game.playtime_forever / 60).toFixed(2) :
                        displayMode === 'minutes' ? game.playtime_forever :
                        ((game.playtime_forever / totalPlaytime) * 100).toFixed(2);

                      const unit = displayMode === 'percentage' ? '%' : (displayMode === 'hours' ? 'hours' : 'minutes');
                      
                      return (
                        <li key={game.appid} style={{ backgroundColor: darkMode ? '#2e2e2e' : '#f8f9fa', padding: '10px', margin: '5px 0', borderRadius: '4px' }}>
                          {game.name} - {playtime} {unit}
                        </li>
                      );
                    })
                ) : (
                  <li style={{ backgroundColor: darkMode ? '#2e2e2e' : '#f8f9fa', padding: '10px', margin: '5px 0', borderRadius: '4px' }}>No data available</li>
                )}
              </ul>
            </div>
          </div>
        </div>
        <h2>Genre Distribution by Playtime</h2>
        <div className="PieChart-container">
          <PieChart width={400} height={400}>
            <Pie dataKey="value" isAnimationActive={true} data={genreData.length > 0 ? genreData : [{ name: 'No data', value: 1 }]} cx={200} cy={200} outerRadius={180} fill="#8884d8">
              {genreData.length > 0 ? (
                genreData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))
              ) : (
                <Cell fill="#d3d3d3" />
              )}
            </Pie>
            <Tooltip formatter={(value, name) => [
              displayMode === 'percentage' ? `${value.toFixed(2)}%` : `${value.toFixed(2)} ${displayMode}`,
              `Genre: ${name}`
            ]} />
          </PieChart>
        </div>
      </header>
      <footer style={{ backgroundColor: darkMode ? '#1e1e1e' : '#ffffff', color: darkMode ? '#ffffff' : '#000000', padding: '10px', textAlign: 'center', marginTop: '20px' }}>
        <p>Steam Analytics App - {new Date().getFullYear()}</p>
      </footer>
    </div>
  );
}

export default App;