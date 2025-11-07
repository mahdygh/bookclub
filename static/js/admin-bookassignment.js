document.addEventListener('DOMContentLoaded', function () {
    initAssignmentChangeListToggle();
    initAssignmentFormHelpers();
});

function initAssignmentChangeListToggle() {
    const toggleButton = document.getElementById('toggle-completed-assignments');
    const resultTable = document.getElementById('result_list');

    if (!toggleButton || !resultTable) {
        return;
    }

    const completedRows = Array.from(resultTable.querySelectorAll('tbody tr')).filter(function (row) {
        const statusCell = row.querySelector('.field-status');
        return statusCell && statusCell.textContent.includes('تکمیل');
    });

    completedRows.forEach(function (row) {
        row.classList.add('row-completed');
    });

    let visible = false;

    const updateState = function () {
        if (visible) {
            resultTable.classList.add('show-completed');
            toggleButton.textContent = 'مخفی کردن امانت‌های تکمیل‌شده';
        } else {
            resultTable.classList.remove('show-completed');
            toggleButton.textContent = 'نمایش امانت‌های تکمیل‌شده';
        }
    };

    updateState();

    toggleButton.addEventListener('click', function () {
        visible = !visible;
        updateState();
    });
}

function initAssignmentFormHelpers() {
    if (!window.bookAssignmentData) {
        return;
    }

    const memberSelect = document.getElementById('id_member');
    const bookSelect = document.getElementById('id_book');
    const assignedInput = document.getElementById('id_assigned_date');
    const dueInput = document.getElementById('id_due_date');
    const quizInput = document.getElementById('id_quiz_score_earned');

    if (!bookSelect || !assignedInput || !dueInput) {
        return;
    }

    const meta = window.bookAssignmentData;
    const booksData = meta.books || [];
    const membersData = meta.members || [];
    const defaultNow = meta.now || '';
    const currentBookId = meta.current_book_id ? String(meta.current_book_id) : '';
    const currentMemberId = meta.current_member_id ? String(meta.current_member_id) : '';
    const maxInitialOptions = Number(meta.max_initial_options || 3);

    const booksMap = {};
    booksData.forEach(function (book) {
        booksMap[String(book.id)] = book;
    });

    const membersMap = {};
    membersData.forEach(function (member) {
        const entry = Object.assign({}, member);
        entry.stage_book_ids = (entry.stage_book_ids || []).map(String);
        entry.available_book_ids = (entry.available_book_ids || []).map(String);
        entry.completed_book_ids = (entry.completed_book_ids || []).map(String);
        membersMap[String(member.id)] = entry;
    });

    if (memberSelect && !memberSelect.value && currentMemberId) {
        memberSelect.value = currentMemberId;
    }

    if (!assignedInput.value && defaultNow) {
        assignedInput.value = defaultNow;
    }

    let quizHint = document.getElementById('quiz-base-hint');
    if (quizInput && !quizHint) {
        quizHint = document.createElement('div');
        quizHint.id = 'quiz-base-hint';
        quizHint.className = 'field-hint';
        const quizWrapper = quizInput.closest('.form-row');
        if (quizWrapper) {
            const box = quizWrapper.querySelector('.field-box') || quizWrapper;
            box.appendChild(quizHint);
        }
    }

    let dueHint = document.getElementById('due-date-hint');
    if (!dueHint) {
        dueHint = document.createElement('div');
        dueHint.id = 'due-date-hint';
        dueHint.className = 'field-hint';
        const dueWrapper = dueInput.closest('.form-row');
        if (dueWrapper) {
            const box = dueWrapper.querySelector('.field-box') || dueWrapper;
            box.appendChild(dueHint);
        }
    }

    if (quizInput) {
        const currentValue = quizInput.value && quizInput.value.trim();
        quizInput.dataset.userEdited = currentValue && currentValue !== '0' ? 'true' : 'false';
    }

    const getBookData = function (bookId) {
        if (!bookId) {
            return null;
        }
        return booksMap[String(bookId)] || null;
    };

    const formatDateTimeLocal = function (dateObj) {
        if (!(dateObj instanceof Date) || Number.isNaN(dateObj.getTime())) {
            return '';
        }
        const tzOffset = dateObj.getTimezoneOffset() * 60000;
        const localISOTime = new Date(dateObj.getTime() - tzOffset).toISOString();
        return localISOTime.slice(0, 16);
    };

    const updateQuizHint = function () {
        if (!quizHint) {
            return;
        }
        const bookData = getBookData(bookSelect.value);
        if (bookData) {
            quizHint.textContent = `امتیاز پایه آزمون برای این کتاب: ${bookData.quiz_score}`;
        } else {
            quizHint.textContent = '';
        }
    };

    const updateQuizValue = function (force) {
        if (!quizInput) {
            return;
        }
        const bookData = getBookData(bookSelect.value);
        if (!bookData) {
            return;
        }

        if (!force && quizInput.dataset.userEdited === 'true') {
            return;
        }

        quizInput.value = bookData.quiz_score;
        quizInput.dataset.userEdited = 'false';
    };

    const updateDueHint = function () {
        if (!dueHint) {
            return;
        }
        const bookData = getBookData(bookSelect.value);
        if (bookData && bookData.reading_days) {
            dueHint.textContent = `مهلت مطالعه کتاب: ${bookData.reading_days} روز`;
        } else {
            dueHint.textContent = '';
        }
    };

    const updateDueDate = function (force) {
        const bookData = getBookData(bookSelect.value);
        if (!bookData || !bookData.reading_days) {
            return;
        }

        const assignedValue = assignedInput.value || defaultNow;
        if (!assignedValue) {
            return;
        }

        const assignedDate = new Date(assignedValue);
        if (Number.isNaN(assignedDate.getTime())) {
            return;
        }

        if (!force && dueInput.dataset.userEdited === 'true') {
            return;
        }

        const dueDate = new Date(assignedDate.getTime());
        dueDate.setDate(dueDate.getDate() + Number(bookData.reading_days));
        dueInput.value = formatDateTimeLocal(dueDate);
        dueInput.dataset.userEdited = 'false';
    };

    dueInput.dataset.userEdited = dueInput.value ? 'true' : 'false';

    assignedInput.addEventListener('change', function () {
        updateDueDate(false);
    });

    dueInput.addEventListener('input', function () {
        dueInput.dataset.userEdited = 'true';
    });

    if (quizInput) {
        quizInput.addEventListener('input', function () {
            quizInput.dataset.userEdited = 'true';
        });
    }

    const getAllowedBookIds = function (memberId) {
        const data = membersMap[String(memberId)] || null;
        if (!data) {
            return [];
        }
        const allowed = data.available_book_ids.slice();
        if (currentBookId && data.stage_book_ids.includes(currentBookId)) {
            if (!allowed.includes(currentBookId)) {
                allowed.push(currentBookId);
            }
        }
        return allowed;
    };

    let showAllButton = null;

    const ensureShowAllButton = function () {
        if (showAllButton) {
            return showAllButton;
        }
        const wrapper = bookSelect.parentElement;
        if (!wrapper) {
            return null;
        }
        showAllButton = document.createElement('button');
        showAllButton.type = 'button';
        showAllButton.id = 'show-all-books-btn';
        showAllButton.className = 'btn show-all-books-btn';
        showAllButton.textContent = 'نمایش همه کتاب‌ها';
        showAllButton.style.marginTop = '8px';
        showAllButton.addEventListener('click', function (event) {
            event.preventDefault();
            const expanded = bookSelect.dataset.extraVisible === 'true';
            setExtraVisibility(!expanded);
        });
        wrapper.appendChild(showAllButton);
        return showAllButton;
    };

    const setExtraVisibility = function (expand) {
        const extraOptions = Array.from(bookSelect.options).filter(function (option) {
            return option.dataset.extra === 'true';
        });
        extraOptions.forEach(function (option) {
            option.hidden = !expand;
        });
        bookSelect.dataset.extraVisible = expand ? 'true' : 'false';
        if (showAllButton) {
            showAllButton.textContent = expand ? 'نمایش کمتر' : 'نمایش همه کتاب‌ها';
        }
    };

    const rebuildBookOptions = function (allowedIds, preserveSelection) {
        const previousValue = preserveSelection ? bookSelect.value : '';

        while (bookSelect.options.length > 0) {
            bookSelect.remove(0);
        }

        if (allowedIds.length === 0) {
            const emptyOption = document.createElement('option');
            emptyOption.value = '';
            emptyOption.textContent = 'کتابی برای این مرحله موجود نیست';
            emptyOption.disabled = true;
            emptyOption.selected = true;
            bookSelect.appendChild(emptyOption);
            bookSelect.dispatchEvent(new Event('change'));
            return;
        }

        const placeholder = document.createElement('option');
        placeholder.value = '';
        placeholder.textContent = 'یک کتاب را انتخاب کنید';
        bookSelect.appendChild(placeholder);

        const primaryIds = allowedIds.slice(0, Math.max(0, maxInitialOptions));
        const extraIds = allowedIds.slice(primaryIds.length);

        const createOption = function (id, isExtra) {
            const bookData = booksMap[String(id)];
            if (!bookData) {
                return null;
            }
            const option = document.createElement('option');
            option.value = String(id);
            const available = typeof bookData.available_copies === 'number' ? bookData.available_copies : null;
            const stock = typeof bookData.stock_count === 'number' ? bookData.stock_count : null;
            let label = bookData.title || ('کتاب #' + id);
            if (available !== null) {
                label += ` (نسخه موجود: ${available})`;
            } else if (stock !== null) {
                label += ` (موجودی: ${stock})`;
            }
            option.textContent = label;
            if (isExtra) {
                option.dataset.extra = 'true';
            }
            bookSelect.appendChild(option);
            return option;
        };

        primaryIds.forEach(function (id) {
            createOption(id, false);
        });

        extraIds.forEach(function (id) {
            createOption(id, true);
        });

        const extraOptions = Array.from(bookSelect.options).filter(function (option) {
            return option.dataset.extra === 'true';
        });

        if (extraOptions.length > 0) {
            ensureShowAllButton();
            const shouldExpand = previousValue && extraIds.includes(previousValue);
            setExtraVisibility(shouldExpand);
            showAllButton.style.display = '';
        } else if (showAllButton) {
            showAllButton.style.display = 'none';
            setExtraVisibility(true);
        }

        if (previousValue && allowedIds.includes(previousValue)) {
            bookSelect.value = previousValue;
        } else {
            bookSelect.value = '';
        }

        bookSelect.dispatchEvent(new Event('change'));
    };

    const updateBooksForMember = function (memberId, preserveSelection) {
        if (!memberId) {
            while (bookSelect.options.length > 0) {
                bookSelect.remove(0);
            }
            const promptOption = document.createElement('option');
            promptOption.value = '';
            promptOption.textContent = 'ابتدا عضو را انتخاب کنید';
            promptOption.disabled = true;
            promptOption.selected = true;
            bookSelect.appendChild(promptOption);
            bookSelect.dispatchEvent(new Event('change'));
            return;
        }

        const allowed = getAllowedBookIds(memberId);
        rebuildBookOptions(allowed, preserveSelection);
    };

    if (memberSelect) {
        memberSelect.addEventListener('change', function () {
            updateBooksForMember(memberSelect.value, false);
        });
    }

    bookSelect.addEventListener('change', function () {
        dueInput.dataset.userEdited = 'false';
        updateDueHint();
        updateQuizHint();
        updateDueDate(true);
        updateQuizValue(true);
    });

    const initialMemberId = memberSelect ? memberSelect.value : currentMemberId;
    updateBooksForMember(initialMemberId, true);
    updateDueDate(false);
    updateDueHint();
    updateQuizHint();
    updateQuizValue(false);
}

