CREATE USER 'python_user'@'localhost' IDENTIFIED BY 'password';

SET GLOBAL net_read_timeout = 120;
SET GLOBAL net_write_timeout = 120;
SET GLOBAL wait_timeout = 300;


GRANT SELECT, INSERT, UPDATE, DELETE, CREATE ON chatbot.* TO 'python_user'@'localhost';

GRANT ALL PRIVILEGES ON employees.* TO 'python_user'@'localhost';
FLUSH PRIVILEGES;
    
GRANT RELOAD ON *.* TO 'python_user'@'localhost';
FLUSH PRIVILEGES;


use chatbot;
select * from users;


use employees;
SELECT 
    d.dept_name AS department_name,
    AVG(s.salary) AS average_salary
FROM 
    salaries s
JOIN 
    dept_emp de ON s.emp_no = de.emp_no
JOIN 
    departments d ON de.dept_no = d.dept_no
GROUP BY 
    d.dept_name;
    
    
SELECT 
    e.first_name, e.last_name, s.salary, d.dept_name
FROM
    employees e
        JOIN
    salaries s ON e.emp_no = s.emp_no
        JOIN
    dept_emp de ON e.emp_no = de.emp_no
        JOIN
    departments d ON de.dept_no = d.dept_no
WHERE
    s.salary = (SELECT 
            MAX(salary)
        FROM
            salaries);
            
            
use employees;
SELECT 
    d.dept_name,
    e.first_name,
    e.last_name,
    s.salary
FROM employees e
JOIN dept_emp de ON e.emp_no = de.emp_no
JOIN departments d ON de.dept_no = d.dept_no
JOIN (
    SELECT emp_no, MAX(salary) AS max_salary
    FROM salaries
    GROUP BY emp_no
) ms ON e.emp_no = ms.emp_no
JOIN salaries s ON s.emp_no = ms.emp_no AND s.salary = ms.max_salary
ORDER BY d.dept_name, s.salary DESC
LIMIT 0, 1000;



SELECT d.dept_name, e.first_name, e.last_name, s.salary FROM employees e 
JOIN dept_emp de ON e.emp_no = de.emp_no 
JOIN departments d ON de.dept_no = d.dept_no 
JOIN salaries s ON e.emp_no = s.emp_no 
WHERE s.salary = (
    SELECT MAX(salary) FROM salaries s2 WHERE s2.emp_no = e.emp_no
) 
GROUP BY d.dept_no, e.emp_no, s.salary 
ORDER BY d.dept_name, s.salary DESC;

SELECT d.dept_name, e.first_name, e.last_name, avg(s.salary)
FROM employees e
JOIN salaries s ON e.emp_no = s.emp_no
JOIN dept_emp de ON e.emp_no = de.emp_no
JOIN departments d ON de.dept_no = d.dept_no
GROUP BY d.dept_name,
e.first_name, e.last_name;
-- WHERE s.salary = (SEL-- E-- CT MAX(salary) FROM salaries s2 JOIN dept_emp de2 ON s2.emp_no = de2.emp_no WHERE de2.dept_no = de.dept_no)






WITH dept_max_salary AS (
    SELECT 
        de.dept_no,
        MAX(s.salary) AS max_salary
    FROM dept_emp de
    JOIN salaries s ON de.emp_no = s.emp_no
    GROUP BY de.dept_no
)
SELECT 
    d.dept_name,
    e.first_name,
    e.last_name,
    s.salary
FROM dept_max_salary dm
JOIN dept_emp de ON dm.dept_no = de.dept_no
JOIN employees e ON de.emp_no = e.emp_no
JOIN salaries s ON e.emp_no = s.emp_no AND s.salary = dm.max_salary
JOIN departments d ON d.dept_no = dm.dept_no
ORDER BY d.dept_name;


use employees;
SELECT d.dept_name, AVG(s.salary) AS average_salary, COUNT(e.emp_no) AS employee_count
FROM departments d
JOIN dept_emp de ON d.dept_no = de.dept_no
JOIN employees e ON de.emp_no = e.emp_no
JOIN salaries s ON e.emp_no = s.emp_no
GROUP BY d.dept_name
ORDER BY average_salary DESC
LIMIT 1;


SELECT d.dept_name, e.first_name, e.last_name, s.salary 
FROM salaries s 
JOIN employees e ON s.emp_no = e.emp_no 
JOIN dept_emp de ON e.emp_no = de.emp_no 
JOIN departments d ON de.dept_no = d.dept_no 
WHERE s.salary = (SELECT MAX(salary) 
                  FROM salaries s2 
                  JOIN dept_emp de2 ON s2.emp_no = de2.emp_no 
                  WHERE de2.dept_no = de.dept_no) 
ORDER BY d.dept_name;



WITH MaxSalaries AS (
    SELECT de2.dept_no, MAX(s2.salary) AS max_salary
    FROM salaries s2
    JOIN dept_emp de2 ON s2.emp_no = de2.emp_no
    GROUP BY de2.dept_no
),
DeptEmployees AS (
    SELECT d.dept_name, e.first_name, e.last_name, s.salary, de.dept_no
    FROM departments d
    JOIN dept_emp de ON d.dept_no = de.dept_no 
    JOIN salaries s ON de.emp_no = s.emp_no 
    JOIN employees e ON de.emp_no = e.emp_no 
)

SELECT de.dept_name, de.first_name, de.last_name, de.salary 
FROM DeptEmployees de
JOIN MaxSalaries ms ON de.dept_no = ms.dept_no AND de.salary = ms.max_salary
ORDER BY de.dept_name;