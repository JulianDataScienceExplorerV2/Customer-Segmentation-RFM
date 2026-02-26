-- =============================================================================
-- rfm_query.sql — RFM Scoring with Pure SQL
-- =============================================================================
-- EN: Computes RFM (Recency, Frequency, Monetary) scores from a transactions
--     table using window functions (NTILE). Compatible with PostgreSQL,
--     MySQL 8+, BigQuery, Snowflake, and DuckDB.
--
-- ES: Calcula los puntajes RFM desde una tabla de transacciones usando
--     funciones de ventana (NTILE). Compatible con PostgreSQL, MySQL 8+,
--     BigQuery, Snowflake y DuckDB.
-- =============================================================================

-- Step 1 / Paso 1: Aggregate raw RFM metrics per customer
-- -------------------------------------------------------
WITH rfm_raw AS (
    SELECT
        customer_id,

        -- Recency: days since last purchase (lower = more recent = better)
        -- Recencia: dias desde la ultima compra (menor = mas reciente = mejor)
        DATEDIFF(CURRENT_DATE, MAX(purchase_date))  AS recency_days,

        -- Frequency: number of distinct orders
        -- Frecuencia: numero de pedidos distintos
        COUNT(DISTINCT order_id)                    AS frequency,

        -- Monetary: total spend
        -- Monetario: gasto total
        ROUND(SUM(order_value), 2)                  AS monetary

    FROM customer_transactions
    GROUP BY customer_id
),

-- Step 2 / Paso 2: Assign NTILE scores (1-5) using window functions
-- -----------------------------------------------------------------
rfm_scored AS (
    SELECT
        customer_id,
        recency_days,
        frequency,
        monetary,

        -- R score: reversed — fewer days = score 5 (best)
        -- Puntaje R: invertido — menos dias = 5 (mejor)
        NTILE(5) OVER (ORDER BY recency_days DESC)  AS r_score,

        -- F score: more orders = score 5 (best)
        -- Puntaje F: mas pedidos = 5 (mejor)
        NTILE(5) OVER (ORDER BY frequency ASC)      AS f_score,

        -- M score: higher spend = score 5 (best)
        -- Puntaje M: mayor gasto = 5 (mejor)
        NTILE(5) OVER (ORDER BY monetary ASC)       AS m_score

    FROM rfm_raw
),

-- Step 3 / Paso 3: Combine scores and classify segments
-- -----------------------------------------------------
rfm_final AS (
    SELECT
        customer_id,
        recency_days,
        frequency,
        monetary,
        r_score,
        f_score,
        m_score,
        (r_score + f_score + m_score)               AS rfm_total,
        CONCAT(r_score, f_score)                    AS rf_segment_code,

        -- Business segment label / Etiqueta de segmento de negocio
        CASE
            WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4
                THEN 'Champions'
            WHEN f_score >= 4 AND m_score >= 4
                THEN 'Loyal'
            WHEN r_score >= 4 AND f_score <= 2
                THEN 'New Customers'
            WHEN r_score <= 2 AND f_score >= 3 AND m_score >= 3
                THEN 'At Risk'
            WHEN r_score <= 2 AND f_score <= 2
                THEN 'Lost'
            ELSE
                'Potential'
        END AS segment

    FROM rfm_scored
)

-- Final output / Salida final
SELECT
    customer_id,
    recency_days,
    frequency,
    monetary,
    r_score,
    f_score,
    m_score,
    rfm_total,
    segment,

    -- Recommended action / Accion recomendada
    CASE segment
        WHEN 'Champions'     THEN 'Reward & ask for referrals / Recompensa y pide referidos'
        WHEN 'Loyal'         THEN 'Upsell & loyalty program / Upselling y programa de lealtad'
        WHEN 'New Customers' THEN 'Onboard & educate / Onboarding y educacion'
        WHEN 'At Risk'       THEN 'Win-back campaign + discount / Campana de recuperacion'
        WHEN 'Lost'          THEN 'Strong re-engagement offer / Oferta fuerte de reenganche'
        ELSE                      'Nurture with recommendations / Nutrir con recomendaciones'
    END AS recommended_action

FROM rfm_final
ORDER BY rfm_total DESC;


-- =============================================================================
-- Segment distribution view / Vista de distribucion de segmentos
-- =============================================================================
SELECT
    segment,
    COUNT(*)                                                AS customers,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1)     AS pct_customers,
    ROUND(AVG(recency_days), 1)                             AS avg_recency_days,
    ROUND(AVG(frequency), 1)                                AS avg_frequency,
    ROUND(AVG(monetary), 2)                                 AS avg_monetary,
    ROUND(SUM(monetary), 2)                                 AS total_revenue,
    ROUND(SUM(monetary) * 100.0 / SUM(SUM(monetary)) OVER (), 1) AS pct_revenue

FROM rfm_final
GROUP BY segment
ORDER BY total_revenue DESC;
