const duckdb = require('duckdb');
const path = require('path');

// Create a persistent database file in the forecaster folder
const dbPath = path.join(__dirname, 'forecaster', 'data.duckdb');
const db = new duckdb.Database(dbPath);

// Check if table exists, if not create it
db.run(`
    CREATE TABLE IF NOT EXISTS data AS 
    SELECT * FROM read_csv_auto('${path.join(__dirname, 'processed.csv')}')
`);

// Example query - you can modify this query as needed
const query = `
    SELECT * FROM data LIMIT 1000;
`;

db.all(query, (err, rows) => {
    if (err) {
        console.error('Error executing query:', err);
        return;
    }
    console.log('Query results:');
    console.log(rows);
}); 