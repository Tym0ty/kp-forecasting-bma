<template>
  <div class="train-data-page">
    <div class="header-row">
      <h1>Train Data Viewer</h1>
      <span v-if="maxRowsReached" class="max-rows-warning">
        <i class="fas fa-exclamation-triangle"></i>
        Showing first {{ maxRows }} rows only (file too large)
      </span>
    </div>
    <div class="filter-bar">
      <input
        v-model="search"
        class="search-input"
        type="text"
        placeholder="Search in all columns..."
        @input="resetPage"
      />
      <select v-model="filterColumn" class="filter-select" @change="resetPage">
        <option value="">All Columns</option>
        <option v-for="col in columns" :key="col" :value="col">{{ col }}</option>
      </select>
    </div>
    <div v-if="error" class="error">{{ error }}</div>
    <div v-if="loading" class="loading">
      <p>Loading train data...</p>
      <div class="spinner"></div>
    </div>
    <div v-if="filteredData.length" class="result">
      <div class="table-scroll">
        <table class="data-table">
          <thead>
            <tr>
              <th v-for="col in columns" :key="col">{{ col }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, idx) in paginatedData" :key="idx">
              <td v-for="col in columns" :key="col">{{ row[col] }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="controls-row">
        <div class="pagination-controls" v-if="totalPages > 1">
          <button class="pagination-button" @click="prevPage" :disabled="currentPage === 1">
            <i class="fas fa-chevron-left"></i> Previous
          </button>
          <span class="page-info">Page {{ currentPage }} of {{ totalPages }}</span>
          <button class="pagination-button" @click="nextPage" :disabled="currentPage === totalPages">
            Next <i class="fas fa-chevron-right"></i>
          </button>
        </div>
        <div class="page-size-controls">
          <label>
            Rows per page:
            <select v-model.number="itemsPerPage" @change="resetPage">
              <option v-for="n in [25,50,100,200,500]" :key="n" :value="n">{{ n }}</option>
            </select>
          </label>
        </div>
      </div>
    </div>
    <div v-if="!loading && !filteredData.length && !error" class="empty">
      <p>No data to display.</p>
    </div>
  </div>
</template>

<script>
export default {
  name: 'TrainDataPage',
  data() {
    return {
      data: [],
      columns: [],
      loading: false,
      error: null,
      currentPage: 1,
      itemsPerPage: 100,
      maxRows: 2000,
      maxRowsReached: false,
      search: '',
      filterColumn: ''
    }
  },
  computed: {
    filteredData() {
      if (!this.search) return this.data;
      const searchLower = this.search.toLowerCase();
      if (this.filterColumn && this.columns.includes(this.filterColumn)) {
        // Filter only on selected column
        return this.data.filter(row =>
          String(row[this.filterColumn]).toLowerCase().includes(searchLower)
        );
      } else {
        // Filter on all columns
        return this.data.filter(row =>
          this.columns.some(col =>
            String(row[col]).toLowerCase().includes(searchLower)
          )
        );
      }
    },
    totalPages() {
      return Math.ceil(this.filteredData.length / this.itemsPerPage);
    },
    paginatedData() {
      const start = (this.currentPage - 1) * this.itemsPerPage;
      return this.filteredData.slice(start, start + this.itemsPerPage);
    }
  },
  methods: {
    prevPage() {
      if (this.currentPage > 1) this.currentPage--;
    },
    nextPage() {
      if (this.currentPage < this.totalPages) this.currentPage++;
    },
    resetPage() {
      this.currentPage = 1;
    },
    parseCSV(text, maxRows) {
      const rows = [];
      let row = [];
      let field = '';
      let inQuotes = false;
      let rowCount = 0;
      for (let i = 0; i < text.length; i++) {
        const char = text[i];
        if (char === '"') {
          if (inQuotes && text[i + 1] === '"') {
            field += '"';
            i++;
          } else {
            inQuotes = !inQuotes;
          }
        } else if (char === ',' && !inQuotes) {
          row.push(field);
          field = '';
        } else if ((char === '\n' || char === '\r') && !inQuotes) {
          if (field !== '' || row.length > 0) row.push(field);
          if (row.length) rows.push(row);
          row = [];
          field = '';
          if (char === '\r' && text[i + 1] === '\n') i++;
          rowCount++;
          if (rowCount > maxRows) break;
        } else {
          field += char;
        }
      }
      if ((field !== '' || row.length > 0) && rowCount <= maxRows) {
        row.push(field);
        rows.push(row);
      }
      return rows;
    },
    async fetchTrainData() {
      this.loading = true
      this.error = null
      this.data = []
      this.columns = []
      this.maxRowsReached = false
      try {
        let url = 'http://localhost:8000/all-train-data/';
        const response = await fetch(url, {
          method: 'GET',
          headers: {
            'Accept': 'text/csv'
          }
        });
        if (!response.ok) throw new Error('Failed to fetch train data');
        const csvText = await response.text();

        // Only parse the first maxRows rows to avoid memory issues
        const rows = this.parseCSV(csvText.trim(), this.maxRows);
        if (rows.length < 2) {
          this.data = [];
          this.columns = [];
        } else {
          const headers = rows[0];
          this.columns = headers;
          this.data = rows.slice(1).map(row => {
            const obj = {};
            headers.forEach((header, idx) => {
              // Fill null/empty with NaN
              obj[header] = (row[idx] === undefined || row[idx] === null || row[idx] === '') ? 'NaN' : row[idx];
            });
            return obj;
          });
          // If we hit the maxRows limit, show a warning
          if (rows.length - 1 >= this.maxRows) {
            this.maxRowsReached = true;
          }
        }
      } catch (err) {
        this.error = 'Failed to fetch or parse train data.';
      } finally {
        this.loading = false;
      }
    }
  },
  mounted() {
    this.fetchTrainData();
  },
  watch: {
    currentPage(val) {
      if (val < 1) this.currentPage = 1;
      if (val > this.totalPages) this.currentPage = this.totalPages;
    }
  }
}
</script>

<style scoped>
.train-data-page {
  padding: 2rem;
  background: #f9f9f9;
  min-height: 100vh;
  font-family: 'Segoe UI', Arial, sans-serif;
}
.header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 2rem;
  margin-bottom: 1.5rem;
}
.header-row h1 {
  margin: 0;
  font-size: 2rem;
  color: #2c3e50;
  font-weight: 600;
}
.max-rows-warning {
  color: #e67e22;
  font-size: 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: #fff3cd;
  border: 1px solid #ffeeba;
  border-radius: 4px;
  padding: 0.5rem 1rem;
}
.filter-bar {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.2rem;
  background: #fff;
  padding: 1rem 1.5rem;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(44,62,80,0.04);
}
.search-input {
  flex: 1;
  padding: 0.6rem 1rem;
  border-radius: 4px;
  border: 1px solid #ddd;
  font-size: 1rem;
  background: #f9f9f9;
}
.filter-select {
  padding: 0.6rem 1rem;
  border-radius: 4px;
  border: 1px solid #ddd;
  font-size: 1rem;
  background: #f9f9f9;
}
.result {
  background: #fff;
  padding: 1.5rem;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}
.table-scroll {
  overflow-x: auto;
  max-width: 100vw;
}
.data-table {
  width: 100%;
  min-width: 700px;
  border-collapse: collapse;
  margin-top: 0.5rem;
  background: #fff;
}
.data-table th, .data-table td {
  padding: 10px 14px;
  border-bottom: 1px solid #e0e0e0;
  text-align: left;
  font-size: 0.98rem;
}
.data-table th {
  background: #4CAF50;
  color: #fff;
  font-weight: 500;
  position: sticky;
  top: 0;
  z-index: 1;
}
.data-table tr:nth-child(even) {
  background: #f7fafc;
}
.data-table tr:hover {
  background: #e8f5e9;
}
.loading, .error, .empty {
  text-align: center;
  margin: 2rem 0;
}
.spinner {
  width: 40px;
  height: 40px;
  margin: 1rem auto;
  border: 5px solid #f3f3f3;
  border-top: 5px solid #4CAF50;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}
@keyframes spin {
  0% { transform: rotate(0deg);}
  100% { transform: rotate(360deg);}
}
.controls-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 1.5rem;
  flex-wrap: wrap;
  gap: 1rem;
}
.pagination-controls {
  display: flex;
  align-items: center;
  gap: 1rem;
}
.pagination-button {
  padding: 0.5rem 1.2rem;
  background: #4CAF50;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: background 0.2s;
}
.pagination-button:disabled {
  background: #ccc;
  cursor: not-allowed;
}
.page-info {
  font-size: 1rem;
  color: #333;
}
.page-size-controls {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1rem;
}
select {
  padding: 0.3rem 0.7rem;
  border-radius: 4px;
  border: 1px solid #ddd;
  font-size: 1rem;
  background: #f9f9f9;
}
</style>
