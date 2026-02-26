import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("C:/tmp/rfm/data/customer_segments.csv")

plt.style.use('dark_background')
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')

# Custom color mapping to match the portfolio feeling
color_map = {
    'Champions': '#00ff9d', # Green
    'Loyal': '#00e5ff',     # Cyan
    'At Risk': '#ffb700',   # Yellow
    'Potential': '#a855f7', # Purple
    'Lost': '#ff3366'       # Red
}

ax.xaxis.pane.fill = False
ax.yaxis.pane.fill = False
ax.zaxis.pane.fill = False

for segment, color in color_map.items():
    subset = df[df['segment'] == segment]
    ax.scatter(subset['recency'], subset['frequency'], subset['monetary'], 
               c=color, label=segment, s=40, alpha=0.8, edgecolor='#000000', linewidth=0.3)

ax.set_xlabel('Recency (Days)')
ax.set_ylabel('Frequency (Orders)')
ax.set_zlabel('Monetary (Spend)')
ax.set_title('RFM Customer Segments (K-Means)', fontsize=16, pad=20)

plt.legend(title='Segments', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()

plt.savefig('C:/tmp/rfm/data/clusters_3d.png', dpi=300, bbox_inches='tight', transparent=True)
print("Saved 3D plot to C:/tmp/rfm/data/clusters_3d.png")
