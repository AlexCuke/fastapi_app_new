# -*- coding: utf-8 -*-

DEFAULT_TEMPLATES = [
    {
        "name": "Отменить отметку о процедуре (unmarkProcedureCancelling)",
        "method": "POST",
        "path": "/api/v1/procedure/unmarkProcedureCancelling",
        "payload": {
            "assignmentCompositionUid": "@config:assignmentCompositionUid",
            "code": "@config:code",
            "workplaceId": "@config:workplaceId",
            "doctorName": "@config:doctorName",
            "doctorJob": "@config:doctorJob"
        }
    },
    {
        "name": "Откатить завершённую процедуру (rollbackCompleteProcedure)",
        "method": "POST",
        "path": "/api/v1/procedure/rollbackCompleteProcedure",
        "payload": {
            "assignmentCompositionUid": "@config:assignmentCompositionUid",
            "code": "@config:code",
            "workplaceId": "@config:workplaceId",
            "doctorName": "@config:doctorName",
            "doctorJob": "@config:doctorJob",
            "updated": "@now_iso"
        }
    },
    {
        "name": "Откатить отмену процедуры (rollbackCancelProcedure)",
        "method": "POST",
        "path": "/api/v1/procedure/rollbackCancelProcedure",
        "payload": {
            "assignmentCompositionUid": "@config:assignmentCompositionUid",
            "code": "@config:code",
            "workplaceId": "@config:workplaceId",
            "doctorName": "@config:doctorName",
            "doctorJob": "@config:doctorJob",
            "updated": "@now_iso"
        }
    },
    {
        "name": "Запланировать процедуру (planProcedure)",
        "method": "POST",
        "path": "/api/v1/procedure/planProcedure",
        "payload": {
            "assignmentCompositionUid": "@config:assignmentCompositionUid",
            "code": "@config:code",
            "planningDate": "@now_iso",
            "dayTimePeriod": "@config:dayTimePeriod",
            "procedureDressing": "@config:procedureDressing",
            "isDoctor": "@config:isDoctor",
            "room": "@config:room",
            "deviceId": "@config:deviceId",
            "workplaceId": "@config:workplaceId",
            "doctorName": "@config:doctorName",
            "doctorJob": "@config:doctorJob",
            "cito": "@config:cito",
            "updated": "@now_iso"
        }
    },
    {
        "name": "Отметить процедуру как отменяемую (markProcedureCancelling)",
        "method": "POST",
        "path": "/api/v1/procedure/markProcedureCancelling",
        "payload": {
            "assignmentCompositionUid": "@config:assignmentCompositionUid",
            "code": "@config:code",
            "workplaceId": "@config:workplaceId",
            "doctorName": "@config:doctorName",
            "doctorJob": "@config:doctorJob",
            "byExecutor": "@config:byExecutor"
        }
    },
    {
        "name": "Получить список процедур (getProcedures)",
        "method": "POST",
        "path": "/api/v1/procedure/getProcedures",
        "payload": {
            "statuses": ["PLANNED", "IN_PROGRESS"],
            "careCaseId": ["@config:careCaseId"],
            "patientId": ["@config:patientId"],
            "ehrId": ["@config:ehrId"],
            "assignmentIds": ["@config:assignmentId"],
            "assignmentCompositionUids": ["@config:assignmentCompositionUid"],
            "assignmentStatuses": ["CREATED", "ASSIGNED"],
            "assignmentName": "@config:assignmentName",
            "dayTimePeriod": ["MORNING", "AFTERNOON"],
            "dateFrom": "@now_iso",
            "dateTo": "@now_iso",
            "sorting": {"field": "planningDate", "direction": "asc"}
        }
    },
    {
        "name": "Деактивировать процедуру (deactivateProcedure)",
        "method": "POST",
        "path": "/api/v1/procedure/deactivateProcedure",
        "payload": {
            "assignmentCompositionUid": "@config:assignmentCompositionUid",
            "code": "@config:code",
            "workplaceId": "@config:workplaceId",
            "doctorName": "@config:doctorName",
            "doctorJob": "@config:doctorJob",
            "updated": "@now_iso"
        }
    },
    {
        "name": "Завершить процедуру с протоколом (completeWithProtocolProcedure)",
        "method": "POST",
        "path": "/api/v1/procedure/completeWithProtocolProcedure",
        "payload": {
            "assignmentCompositionUid": "@config:assignmentCompositionUid",
            "code": "@config:code",
            "workplaceId": "@config:workplaceId",
            "doctorName": "@config:doctorName",
            "doctorJob": "@config:doctorJob",
            "resultCompositionUid": "@config:resultCompositionUid",
            "description": "@config:description",
            "procedureDressing": "@config:procedureDressing",
            "updated": "@now_iso"
        }
    },
    {
        "name": "Завершить процедуру (completeProcedure)",
        "method": "POST",
        "path": "/api/v1/procedure/completeProcedure",
        "payload": {
            "assignmentCompositionUid": "@config:assignmentCompositionUid",
            "code": "@config:code",
            "workplaceId": "@config:workplaceId",
            "doctorName": "@config:doctorName",
            "doctorJob": "@config:doctorJob",
            "resultCompositionUid": "@config:resultCompositionUid",
            "description": "@config:description",
            "procedureDressing": "@config:procedureDressing",
            "updated": "@now_iso"
        }
    },
    {
        "name": "Отменить процедуру (cancelProcedure)",
        "method": "POST",
        "path": "/api/v1/procedure/cancelProcedure",
        "payload": {
            "assignmentCompositionUid": "@config:assignmentCompositionUid",
            "code": "@config:code",
            "workplaceId": "@config:workplaceId",
            "doctorName": "@config:doctorName",
            "doctorJob": "@config:doctorJob",
            "byExecutor": "@config:byExecutor",
            "resultCompositionUid": "@config:resultCompositionUid",
            "updated": "@now_iso"
        }
    },
    {
        "name": "Активировать процедуру с протоколом (activateWithProtocolProcedure)",
        "method": "POST",
        "path": "/api/v1/procedure/activateWithProtocolProcedure",
        "payload": {
            "assignmentCompositionUid": "@config:assignmentCompositionUid",
            "code": "@config:code",
            "workplaceId": "@config:workplaceId",
            "doctorName": "@config:doctorName",
            "doctorJob": "@config:doctorJob",
            "updated": "@now_iso"
        }
    },
    {
        "name": "Активировать процедуру (activateProcedure)",
        "method": "POST",
        "path": "/api/v1/procedure/activateProcedure",
        "payload": {
            "assignmentCompositionUid": "@config:assignmentCompositionUid",
            "code": "@config:code",
            "workplaceId": "@config:workplaceId",
            "doctorName": "@config:doctorName",
            "doctorJob": "@config:doctorJob",
            "updated": "@now_iso"
        }
    },
    {
        "name": "Создать назначение (assignment)",
        "method": "POST",
        "path": "/api/v1/assignment",
        "payload": {
            "ehrId": "@config:ehrId",
            "patientId": "@config:patientId",
            "careCaseId": "@config:careCaseId",
            "assignmentCompositionUid": "@config:assignmentCompositionUid",
            "assignmentCode": "@config:assignmentCode",
            "assignmentName": "@config:assignmentName",
            "workplaceId": "@config:workplaceId",
            "doctorName": "@config:doctorName",
            "doctorJob": "@config:doctorJob",
            "assigneeId": "@config:assigneeId",
            "assigneeName": "@config:assigneeName",
            "cito": "@config:cito",
            "assignmentDate": "@now_iso",
            "updated": "@now_iso",
            "created": "@now_iso",
            "effectArea": "@config:effectArea",
            "schedule": [{
                "code": "@config:scheduleCode",
                "planningDate": "@now_iso",
                "periodCode": "@config:periodCode",
                "procedureDressing": "@config:procedureDressing",
                "isDoctor": "@config:isDoctor",
                "room": "@config:room",
                "deviceId": "@config:deviceId"
            }],
            "procedureCount": "@config:procedureCount",
            "pmuNaz": "@config:pmuNaz"
        }
    },
    {
        "name": "Снять отметку о завершении назначения (unmarkProcedureAssignmentAsFinishing)",
        "method": "POST",
        "path": "/api/v1/assignment/unmarkProcedureAssignmentAsFinishing",
        "payload": {
            "assignmentCompositionUid": "@config:assignmentCompositionUid",
            "updated": "@now_iso",
            "workplaceId": "@config:workplaceId",
            "doctorName": "@config:doctorName",
            "doctorJob": "@config:doctorJob"
        }
    },
    {
        "name": "Снять отметку об отмене назначения (unmarkAssignmentAsCancelling)",
        "method": "POST",
        "path": "/api/v1/assignment/unmarkAssignmentAsCancelling",
        "payload": {
            "assignmentCompositionUid": "@config:assignmentCompositionUid",
            "workplaceId": "@config:workplaceId",
            "doctorName": "@config:doctorName",
            "doctorJob": "@config:doctorJob"
        }
    },
    {
        "name": "Откатить завершение назначения (rollbackComplete)",
        "method": "POST",
        "path": "/api/v1/assignment/rollbackComplete",
        "payload": {
            "assignmentCompositionUid": "@config:assignmentCompositionUid",
            "updated": "@now_iso",
            "workplaceId": "@config:workplaceId",
            "doctorName": "@config:doctorName",
            "doctorJob": "@config:doctorJob"
        }
    },
    {
        "name": "Откатить отмену назначения (rollbackCancelProcedureAssignment)",
        "method": "POST",
        "path": "/api/v1/assignment/rollbackCancelProcedureAssignment",
        "payload": {
            "assignmentCompositionUid": "@config:assignmentCompositionUid",
            "updated": "@now_iso",
            "workplaceId": "@config:workplaceId",
            "doctorName": "@config:doctorName",
            "doctorJob": "@config:doctorJob"
        }
    },
    {
        "name": "Запланировать назначение (plan) - полный",
        "method": "POST",
        "path": "/api/v1/assignment/plan",
        "payload": {
            "ehrId": "@config:ehrId",
            "patientId": "@config:patientId",
            "careCaseId": "@config:careCaseId",
            "assignmentCompositionUid": "@config:assignmentCompositionUid",
            "assignmentCode": "@config:assignmentCode",
            "assignmentName": "@config:assignmentName",
            "workplaceId": "@config:workplaceId",
            "doctorName": "@config:doctorName",
            "doctorJob": "@config:doctorJob",
            "assigneeId": "@config:assigneeId",
            "assigneeName": "@config:assigneeName",
            "cito": "@config:cito",
            "assignmentDate": "@now_iso",
            "updated": "@now_iso",
            "created": "@now_iso",
            "effectArea": "@config:effectArea",
            "schedule": [{
                "code": "@config:scheduleCode",
                "planningDate": "@now_iso",
                "periodCode": "@config:periodCode",
                "procedureDressing": "@config:procedureDressing",
                "isDoctor": "@config:isDoctor",
                "room": "@config:room",
                "deviceId": "@config:deviceId"
            }],
            "procedureCount": "@config:procedureCount"
        }
    },
    {
        "name": "Планирование назначения (plan) с результатом",
        "method": "POST",
        "path": "/api/v1/assignment/plan",
        "payload": {
            "resultCompositionUid": "@config:resultCompositionUid",
            "assignmentCompositionUid": "@config:assignmentCompositionUid",
            "updated": "@now_iso",
            "workplaceId": "@config:workplaceId",
            "doctorName": "@config:doctorName",
            "doctorJob": "@config:doctorJob"
        }
    },
    {
        "name": "Отметить назначение как редактируемое (markAssignmentAsEditing)",
        "method": "POST",
        "path": "/api/v1/assignment/markAssignmentAsEditing",
        "payload": {
            "assignmentCompositionUid": "@config:assignmentCompositionUid",
            "updated": "@now_iso",
            "workplaceId": "@config:workplaceId",
            "doctorName": "@config:doctorName",
            "doctorJob": "@config:doctorJob"
        }
    },
    {
        "name": "Отметить назначение как отменяемое (markAssignmentAsCancelling)",
        "method": "POST",
        "path": "/api/v1/assignment/markAssignmentAsCancelling",
        "payload": {
            "assignmentCompositionUid": "@config:assignmentCompositionUid",
            "byExecutor": "@config:byExecutor",
            "workplaceId": "@config:workplaceId",
            "doctorName": "@config:doctorName",
            "doctorJob": "@config:doctorJob"
        }
    },
    {
        "name": "Найти назначения (find)",
        "method": "POST",
        "path": "/api/v1/assignment/find",
        "payload": {
            "careCaseId": "@config:careCaseId",
            "assignmentIds": ["@config:assignmentId"],
            "assignmentCompositionUids": ["@config:assignmentCompositionUid"],
            "doctorId": "doctor_001",
            "doctorName": "@config:doctorName",
            "assigneeId": "@config:assigneeId",
            "executorId": "@config:executorId",
            "assignmentName": "@config:assignmentName",
            "dateFrom": "@now_iso",
            "dateTo": "@now_iso",
            "sorting": {"field": "assignmentDate", "direction": "asc"}
        }
    },
    {
        "name": "Найти дубликаты назначений (findDuplicates)",
        "method": "POST",
        "path": "/api/v1/assignment/findDuplicates",
        "payload": {
            "careCaseId": "@config:careCaseId",
            "assignmentCode": ["@config:assignmentCode", "ANOTHER_CODE"],
            "statuses": ["CREATED"],
            "period": 7
        }
    },
    {
        "name": "Найти назначения между датами (findBetween)",
        "method": "POST",
        "path": "/api/v1/assignment/findBetween",
        "payload": {
            "patientId": "@config:patientId",
            "ehrId": "@config:ehrId",
            "workplaceId": "@config:workplaceId",
            "dateFrom": "@now_iso",
            "dateTo": "@now_iso"
        }
    },
    {
        "name": "Отметить назначение как выполненное (doneProcedureAssignment)",
        "method": "POST",
        "path": "/api/v1/assignment/doneProcedureAssignment",
        "payload": {
            "assignmentCompositionUid": "@config:assignmentCompositionUid",
            "updated": "@now_iso",
            "byExecutor": "@config:byExecutor",
            "workplaceId": "@config:workplaceId",
            "doctorName": "@config:doctorName",
            "doctorJob": "@config:doctorJob"
        }
    },
    {
        "name": "Удалить назначение (delete)",
        "method": "POST",
        "path": "/api/v1/assignment/delete",
        "payload": {
            "assignmentCompositionUid": "@config:assignmentCompositionUid",
            "updated": "@now_iso",
            "workplaceId": "@config:workplaceId",
            "doctorName": "@config:doctorName",
            "doctorJob": "@config:doctorJob"
        }
    },
    {
        "name": "Деактивировать назначение (deactivateProcedureAssignment)",
        "method": "POST",
        "path": "/api/v1/assignment/deactivateProcedureAssignment",
        "payload": {
            "assignmentCompositionUid": "@config:assignmentCompositionUid",
            "updated": "@now_iso",
            "workplaceId": "@config:workplaceId",
            "doctorName": "@config:doctorName",
            "doctorJob": "@config:doctorJob"
        }
    },
    {
        "name": "Завершить назначение процедуры (completeProcedureAssignment)",
        "method": "POST",
        "path": "/api/v1/assignment/completeProcedureAssignment",
        "payload": {
            "assignmentCompositionUid": "@config:assignmentCompositionUid",
            "resultCompositionUid": "@config:resultCompositionUid",
            "updated": "@now_iso",
            "completed": "@now_iso",
            "workplaceId": "@config:workplaceId",
            "doctorName": "@config:doctorName",
            "doctorJob": "@config:doctorJob"
        }
    },
    {
        "name": "Активировать назначение процедуры (activateProcedureAssignment)",
        "method": "POST",
        "path": "/api/v1/assignment/activateProcedureAssignment",
        "payload": {
            "assignmentCompositionUid": "@config:assignmentCompositionUid",
            "resultCompositionUid": "@config:resultCompositionUid",
            "updated": "@now_iso",
            "workplaceId": "@config:workplaceId",
            "doctorName": "@config:doctorName",
            "doctorJob": "@config:doctorJob"
        }
    },
    {
        "name": "Найти назначение по CompositionUid (GET)",
        "method": "GET",
        "path": "/api/v1/assignment/findByCompositionUid",
        "payload": {
            "compositionUid": "@config:assignmentCompositionUid"
        }
    },
    {
        "name": "Выгрузить в Kafka (ProcedureAssignmentTopic)",
        "method": "KAFKA",
        "path": "ProcedureService_ProcedureAssignmentTopic",
        "payload": {
            "assignmentCompositionUid": "@config:assignmentCompositionUid",
            "assignmentId": "@config:assignmentId",
            "code": "@config:code",
            "procedureCode": "@config:procedureCode",
            "patientId": "@config:patientId",
            "ehrId": "@config:ehrId",
            "updated": "@now_iso",
            "message_source": "fastapi_integration_service"
        }
    }
]