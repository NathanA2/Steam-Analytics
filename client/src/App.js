import React, { useState, useEffect } from 'react';
import { PieChart, Pie, Cell, Tooltip } from 'recharts';
import './App.css';

function App() {
  const [steamId, setSteamId] = useState('');
  const [recentGames, setRecentGames] = useState([]);
  const [allGames, setAllGames] = useState([]);
  const [topAllTimeGames, setTopAllTimeGames] = useState([]);
  const [displayInHours, setDisplayInHours] = useState(true);
  const [loading, setLoading] = useState(false);
  const [dataFetched, setDataFetched] = useState(false);
  const [darkMode, setDarkMode] = useState(false);

  const fetchRecentGames = () => {
    setLoading(true);
    fetch(`http://localhost:5000/steam/recently_played/${steamId}`)
      .then(response => response.json())
      .then(data => {
        setDataFetched(true);
        // Sort games by playtime in the last 2 weeks and take the top 3
        const topRecentGames = data.sort((a, b) => b.playtime_2weeks - a.playtime_2weeks).slice(0, 3);
        setRecentGames(topRecentGames);
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
        // Sort games by total playtime and take the top 3
        const topGames = data.sort((a, b) => b.playtime_forever - a.playtime_forever).slice(0, 3);
        setTopAllTimeGames(topGames);
      })
      .catch(error => console.error('Error fetching all games genres:', error))
      .finally(() => setLoading(false));
  };

  // Prepare data for the pie chart based on playtime per genre
  const genreData = allGames.reduce((acc, game) => {
    game.genres.forEach(genre => {
      const found = acc.find(item => item.name === genre);
      if (found) {
        found.value += displayInHours ? game.playtime_forever / 60 : game.playtime_forever; // Convert minutes to hours if needed
      } else {
        acc.push({ name: genre, value: displayInHours ? game.playtime_forever / 60 : game.playtime_forever }); // Initialize with the correct value
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
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', justifyContent: 'center' }}>
          <label>
            <input
              type="checkbox"
              checked={darkMode}
              onChange={() => setDarkMode(!darkMode)}
            />
            Dark Mode
          </label>
          <label>
            <input
              type="checkbox"
              checked={displayInHours}
              onChange={() => setDisplayInHours(!displayInHours)}
            />
            Display in Hours
          </label>
        </div>
        <div className="TopGames-container" style={{ display: 'flex', justifyContent: 'space-between' }}>
          <div className="TopGames-list" style={{ marginRight: '20px', backgroundColor: darkMode ? '#1e1e1e' : '#ffffff', padding: '10px', borderRadius: '8px' }}>
            <h2>Top Three Most Played Games in Last Two Weeks</h2>
            <ul>
              {dataFetched && recentGames.length === 0 ? (
                Array.from({ length: 3 }).map((_, index) => (
                  <li key={`placeholder-${index}`} style={{ backgroundColor: darkMode ? '#2e2e2e' : '#f8f9fa', padding: '10px', margin: '5px 0', borderRadius: '4px' }}>No games played recently</li>
                ))
              ) : recentGames.length > 0 ? (
                recentGames.map(game => (
                  <li key={game.appid} style={{ backgroundColor: darkMode ? '#2e2e2e' : '#f8f9fa', padding: '10px', margin: '5px 0', borderRadius: '4px' }}>
                    {game.name} - {displayInHours ? (game.playtime_2weeks / 60).toFixed(2) : game.playtime_2weeks} {displayInHours ? 'hours' : 'minutes'}
                  </li>
                ))
              ) : (
                Array.from({ length: 3 }).map((_, index) => (
                  <li key={`placeholder-${index}`} style={{ backgroundColor: darkMode ? '#2e2e2e' : '#f8f9fa', padding: '10px', margin: '5px 0', borderRadius: '4px' }}>No data available</li>
                ))
              )}
            </ul>
          </div>
          <div className="TopGames-list" style={{ backgroundColor: darkMode ? '#1e1e1e' : '#ffffff', padding: '10px', borderRadius: '8px' }}>
            <h2>Top Three Most Played Games of All Time</h2>
            <ul>
              {topAllTimeGames.length > 0 ? (
                topAllTimeGames.map(game => (
                  <li key={game.appid} style={{ backgroundColor: darkMode ? '#2e2e2e' : '#f8f9fa', padding: '10px', margin: '5px 0', borderRadius: '4px' }}>
                    {game.name} - {displayInHours ? (game.playtime_forever / 60).toFixed(2) : game.playtime_forever} {displayInHours ? 'hours' : 'minutes'}
                  </li>
                ))
              ) : (
                Array.from({ length: 3 }).map((_, index) => (
                  <li key={`placeholder-${index}`} style={{ backgroundColor: darkMode ? '#2e2e2e' : '#f8f9fa', padding: '10px', margin: '5px 0', borderRadius: '4px' }}>No data available</li>
                ))
              )}
            </ul>
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
            <Tooltip formatter={(value, name) => [`${value.toFixed(2)} ${displayInHours ? 'hours' : 'minutes'}`, `Genre: ${name}`]} />
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