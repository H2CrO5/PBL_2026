# TA Feedback Investigation: Teacher Material Upload and Lecture Creation

## Test environment

- Branch: `main`
- Commit tested: `c89236d`
- Entry points: the Teacher and Student demo links listed under **Start everything** in the project README
- Teacher account: the provided demo teacher account
- Student integration and Amazon Bedrock: enabled
- Upload format used for the reproduction: Markdown (`.md`)

## Issue 1: Teaching-material file upload appears not to work

### Original feedback

> The teaching-material file upload feature does not seem to be working properly. Please check it.

### Reproduction steps

1. Log in to the Teacher application.
2. Open **Materials / 教材**.
3. Expand **Add Material / 教材を追加**.
4. Select a lecture.
5. Choose a Markdown file using the file uploader.
6. Click **Upload and index / アップロードしてRAGに登録**.
7. Check the Teacher material list and Student RAG synchronization result.

### Observed result

A small Markdown file uploaded successfully:

- `POST /materials/upload` returned HTTP `200`.
- Automatic Student synchronization returned HTTP `200`.
- The material appeared in the Teacher material list.
- Its status was **Available (Bedrock) / 利用可能（Bedrock）**.
- The extracted Markdown content was displayed correctly.

The upload function is therefore not completely broken.

### Problem found

The frontend and backend disagree about the maximum permitted file size:

- The Streamlit upload component displays **200 MB per file**.
- The Teacher API accepts only **20 MB**, controlled by `MAX_MATERIAL_UPLOAD_BYTES`.
- Files larger than 20 MB are rejected with HTTP `413` and `Material file is too large`.

This is a real defect and is a likely explanation if the TA used a lecture PDF or PowerPoint larger than 20 MB.

There is also a usability problem. Selecting a file does not upload it immediately. The user must subsequently click **Upload and index**, and this control is located inside the expanded Add Material section. The required two-step operation may not be obvious.

### Conclusion

**Partially reproduced.** Small supported files work correctly, including Bedrock/RAG synchronization. However, the misleading 200 MB limit and unclear two-step interaction can make the feature appear broken.

The TA's original file was not available, so the exact failure cannot be attributed conclusively to file size, malformed content, or failed text extraction.

### Recommended changes

1. Configure Streamlit to show the same 20 MB limit enforced by the API, or intentionally increase the API limit to 200 MB.
2. Display the actual maximum size next to the upload control.
3. Make the second action explicit, for example: **Step 2: Upload and index this file**.
4. Provide clearer error messages for oversized files, scanned PDFs with no extractable text, malformed PDF/PPTX files, and Student RAG synchronization failures.
5. Add integration tests for all advertised formats: PDF, PPTX, MD, and TXT.

## Issue 2: Unable to add a “講義” from the Teacher “課題作成” screen

### Original feedback

> I couldn’t work out how to add a “講義” from the teacher’s “課題作成” screen.

### Reproduction steps

1. Log in to the Teacher application.
2. Open **Assignment Builder / 課題作成**.
3. Locate the **Lecture / 講義** control.
4. Attempt to add a new lecture.

### Observed result

The screen contains only a dropdown for selecting an existing lecture. It has no:

- **Add Lecture** button;
- lecture creation form;
- navigation link to a lecture-management screen;
- empty-state action when no lectures exist.

### Root cause

Lecture creation is not implemented in the current product flow:

- Assignment Builder calls `GET /materials/lectures`.
- The returned lectures are used only to populate the selection dropdown.
- The backend exposes a lecture-list endpoint but no lecture-creation endpoint.
- Existing lectures are created from seeded demo data.

A teacher consequently cannot add a new “講義” from Assignment Builder or elsewhere in the current Teacher application.

### Conclusion

**Fully reproduced.** The requested operation is currently impossible.

### Recommended changes

1. Add `POST /lectures` or a course-scoped `POST /courses/{course_id}/lectures` endpoint.
2. Add a Teacher UI form for the lecture number, title, and learning objectives.
3. Add **Add Lecture / 講義を追加** next to the lecture dropdown.
4. Automatically select a newly created lecture.
5. Add an actionable empty state: **No lectures are available. Create a lecture before adding materials or assignments.**

If lecture creation is intentionally outside this application's scope, the UI and documentation should explicitly state that lectures are preconfigured by an administrator.

## Resolution

Both findings were addressed on 2026-09-04:

- The upload widget now enforces and displays the same 20 MB limit as the API.
- The upload UI now explains the two required steps.
- Oversized-file API errors include the permitted size.
- Assignment Builder now provides **Add Lecture / 講義を追加**.
- Teachers can enter a lecture number, title, and one or more learning objectives.
- The API verifies course ownership and rejects duplicate lecture numbers.
- A newly created lecture is automatically selected for assignment creation.
- The empty state directs teachers to create a lecture first.

Local verification confirmed that lecture creation returned HTTP `200`, the new lecture was selected immediately, and a Markdown upload still synchronized successfully to Student RAG with Bedrock status available. All Teacher unit tests and all four offline eval gates passed.
