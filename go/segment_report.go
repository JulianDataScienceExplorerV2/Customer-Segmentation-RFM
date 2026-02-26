// segment_report.go — Customer Segment Reporter
// ===============================================
// EN: Reads customer_segments.csv and prints a formatted segment summary
//     table with customer counts, revenue share, and recommended actions.
//
// ES: Lee customer_segments.csv e imprime una tabla resumen de segmentos
//     con conteos de clientes, participacion de revenue y acciones recomendadas.
//
// Usage / Uso:
//   go run go/segment_report.go --file data/customer_segments.csv
//   go run go/segment_report.go --file data/customer_segments.csv --segment Champions
package main

import (
	"encoding/csv"
	"flag"
	"fmt"
	"os"
	"sort"
	"strconv"
	"strings"
	"text/tabwriter"
)

// ── Colors ────────────────────────────────────────────────────────────────────
const (
	reset  = "\033[0m"
	bold   = "\033[1m"
	red    = "\033[31m"
	green  = "\033[32m"
	yellow = "\033[33m"
	cyan   = "\033[36m"
	gray   = "\033[90m"
)

// ── Segment metadata ──────────────────────────────────────────────────────────
var segmentColor = map[string]string{
	"Champions": green + bold,
	"Loyal":     cyan,
	"At Risk":   yellow,
	"Potential": "\033[34m", // blue
	"Lost":      red,
}

var segmentAction = map[string]string{
	"Champions": "Reward & ask for referrals",
	"Loyal":     "Upsell + loyalty program",
	"At Risk":   "Win-back campaign + discount",
	"Potential": "Nurture with recommendations",
	"Lost":      "Strong re-engagement offer",
}

// ── Structs ───────────────────────────────────────────────────────────────────
type SegmentStats struct {
	Name       string
	Count      int
	TotalRev   float64
	AvgRec     float64
	AvgFreq    float64
	AvgMonetary float64
}

// ── CSV loader ────────────────────────────────────────────────────────────────
func loadSegments(path, filterSegment string) (map[string]*SegmentStats, int, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, 0, fmt.Errorf("cannot open file: %w", err)
	}
	defer f.Close()

	r := csv.NewReader(f)
	r.TrimLeadingSpace = true
	rows, err := r.ReadAll()
	if err != nil {
		return nil, 0, fmt.Errorf("CSV parse error: %w", err)
	}
	if len(rows) < 2 {
		return nil, 0, fmt.Errorf("file must have header + data rows")
	}

	// Build header index
	hdr := make(map[string]int)
	for i, h := range rows[0] {
		hdr[strings.ToLower(strings.TrimSpace(h))] = i
	}
	required := []string{"segment", "recency", "frequency", "monetary"}
	for _, col := range required {
		if _, ok := hdr[col]; !ok {
			return nil, 0, fmt.Errorf("missing column: %q", col)
		}
	}

	stats := make(map[string]*SegmentStats)
	total := 0

	for _, row := range rows[1:] {
		seg := strings.TrimSpace(row[hdr["segment"]])
		if filterSegment != "" && !strings.EqualFold(seg, filterSegment) {
			continue
		}
		rec, _ := strconv.ParseFloat(row[hdr["recency"]], 64)
		freq, _ := strconv.ParseFloat(row[hdr["frequency"]], 64)
		mon, _ := strconv.ParseFloat(row[hdr["monetary"]], 64)

		if _, ok := stats[seg]; !ok {
			stats[seg] = &SegmentStats{Name: seg}
		}
		s := stats[seg]
		s.Count++
		s.TotalRev += mon
		s.AvgRec = (s.AvgRec*float64(s.Count-1) + rec) / float64(s.Count)
		s.AvgFreq = (s.AvgFreq*float64(s.Count-1) + freq) / float64(s.Count)
		s.AvgMonetary = (s.AvgMonetary*float64(s.Count-1) + mon) / float64(s.Count)
		total++
	}
	return stats, total, nil
}

// ── Main ──────────────────────────────────────────────────────────────────────
func main() {
	filePath := flag.String("file", "", "Path to customer_segments.csv (required)")
	filterSeg := flag.String("segment", "", "Filter to specific segment (optional)")
	flag.Parse()

	if *filePath == "" {
		fmt.Fprintln(os.Stderr, red+"Error: --file flag is required."+reset)
		fmt.Fprintln(os.Stderr, gray+"Usage: go run go/segment_report.go --file data/customer_segments.csv"+reset)
		os.Exit(1)
	}

	stats, total, err := loadSegments(*filePath, *filterSeg)
	if err != nil {
		fmt.Fprintf(os.Stderr, red+"Error: %v\n"+reset, err)
		os.Exit(1)
	}
	if total == 0 {
		fmt.Fprintln(os.Stderr, yellow+"No customers found."+reset)
		os.Exit(0)
	}

	// Sort: Champions first, then by total revenue
	order := []string{"Champions", "Loyal", "At Risk", "Potential", "Lost"}
	var keys []string
	for _, k := range order {
		if _, ok := stats[k]; ok {
			keys = append(keys, k)
		}
	}
	// Add any unlisted segments
	for k := range stats {
		found := false
		for _, o := range order {
			if k == o {
				found = true
				break
			}
		}
		if !found {
			keys = append(keys, k)
		}
	}
	_ = sort.Search // imported

	// Total revenue
	totalRev := 0.0
	for _, s := range stats {
		totalRev += s.TotalRev
	}

	// Print header
	fmt.Printf("\n%s%s Customer Segment Report%s — %s%s%s\n",
		bold, cyan, reset, gray, *filePath, reset)
	if *filterSeg != "" {
		fmt.Printf("%sFiltered to: %s%s\n", gray, *filterSeg, reset)
	}
	fmt.Printf("%s%d customers · %d segments%s\n\n", gray, total, len(stats), reset)

	// Table
	w := tabwriter.NewWriter(os.Stdout, 0, 0, 3, ' ', 0)
	fmt.Fprintf(w, "%sSegment\tCustomers\tRevenue %%\tAvg Recency\tAvg Orders\tAvg Spend\tAction%s\n",
		bold+cyan, reset)
	fmt.Fprintf(w, "%s%s\t%s\t%s\t%s\t%s\t%s\t%s%s\n",
		gray,
		strings.Repeat("-", 12), strings.Repeat("-", 10), strings.Repeat("-", 10),
		strings.Repeat("-", 12), strings.Repeat("-", 10), strings.Repeat("-", 10),
		strings.Repeat("-", 28), reset)

	for _, key := range keys {
		s := stats[key]
		col := segmentColor[key]
		if col == "" {
			col = reset
		}
		pctRev := s.TotalRev / totalRev * 100
		action := segmentAction[key]
		if action == "" {
			action = "—"
		}
		fmt.Fprintf(w, "%s%-12s%s\t%d (%.0f%%)\t%.1f%%\t%.0f days\t%.1f orders\t$%.0f\t%s%s%s\n",
			col, s.Name, reset,
			s.Count, float64(s.Count)/float64(total)*100,
			pctRev,
			s.AvgRec, s.AvgFreq, s.AvgMonetary,
			gray, action, reset)
	}
	w.Flush()

	// Summary
	fmt.Printf("\n%s%s── Revenue Summary ─────────────────────────────────%s\n", bold, cyan, reset)
	for _, key := range keys {
		s := stats[key]
		col := segmentColor[key]
		if col == "" {
			col = reset
		}
		bar := strings.Repeat("█", int(s.TotalRev/totalRev*30))
		fmt.Printf("  %s%-12s%s %s%-30s%s $%.0f (%.1f%%)\n",
			col, s.Name, reset, green, bar, reset, s.TotalRev, s.TotalRev/totalRev*100)
	}
	fmt.Printf("  %s%-12s%s $%.2f\n", bold, "TOTAL", reset, totalRev)
	fmt.Printf("%s%s────────────────────────────────────────────────────%s\n\n",
		bold, cyan, reset)
}
