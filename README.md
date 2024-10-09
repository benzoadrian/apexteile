-- Delete 100 WooCommerce products from y5vo_posts
DELETE FROM y5vo_posts
WHERE ID IN (
    SELECT ID
    FROM (
        SELECT ID
        FROM y5vo_posts
        WHERE post_type = 'product' 
        AND post_status = 'publish' -- Filter by post status if needed
        ORDER BY ID ASC
        LIMIT 100
    ) AS temp_table
);
