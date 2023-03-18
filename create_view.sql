CREATE OR REPLACE VIEW view1 AS(
	WITH sorted_tasks AS (
	  SELECT *, ROW_NUMBER() OVER (PARTITION BY difficulty, topics ORDER BY title) AS row_num
	  FROM problems
	), numbered_tasks AS (
	  SELECT *, floor((row_num-1)/10.0)+1 AS subset_num
	  FROM sorted_tasks
	)
	SELECT difficulty, topics, subset_num, (
	  SELECT ARRAY_AGG(title ORDER BY title)
	  FROM numbered_tasks
	  WHERE difficulty = t.difficulty
		AND topics = t.topics
		AND subset_num = t.subset_num
	  LIMIT 10
	) AS task_subset
	FROM numbered_tasks t
	GROUP BY difficulty, topics, subset_num
	HAVING COUNT(*) >= 10
)